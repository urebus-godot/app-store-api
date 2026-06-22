from typing import Annotated

from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import Depends, Query, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from app.db.postgres import get_session
from app.core.exceptions import no_rights_exception
from app.core.auth import security, decode_access_token
from app.models.user import UserDB, UserRole
from app.service import user_service

def skip_limit_params(
        skip: Annotated[int, Query(ge=0, lt=99)] = 0, 
        limit: Annotated[int, Query(ge=0, lt=100)] = 10,
        ):
    return skip, limit


async def get_current_user(
    session: SessionDep,   
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UserDB | None:
    """Extract and validate the current user from JWT token."""
    token = credentials.credentials
    payload = decode_access_token(token)
    username = payload.get("sub")

    if username is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, 
            "Invalid token payload"
        )

    user = await user_service.get_user(session, username=username)

    return user


def require_role(role: UserRole):
    def wrapper(user: UserDep):
        if role not in user.roles:
            raise no_rights_exception
        return user
    return wrapper


SessionDep = Annotated[AsyncSession, Depends(get_session)]
UserDep = Annotated[UserDB, Depends(get_current_user)]
PublisherRoleUser = Annotated[UserDB, Depends(require_role(UserRole.PUBLISHER))]
CredentialsDep = Annotated[HTTPAuthorizationCredentials, Depends(security)]
SkipLimitParams = Annotated[tuple[int, int], Depends(skip_limit_params)]
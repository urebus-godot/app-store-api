from __future__ import annotations
from typing import Annotated
from uuid import UUID

from redis.asyncio import Redis
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import Depends, Query
from fastapi.security import OAuth2PasswordBearer

from app.db.postgres import get_session
from app.db.redis import get_redis
from app.core.exceptions import (
    no_rights_exception,
    invalid_token_payload_exception,
)
from app.core.auth import decode_access_token
from app.models.user import UserDB, UserRole

from app.repo.user_repo import UserRepository
from app.repo.app_repo import AppRepository
from app.repo.review_repo import ReviewRepository
from app.repo.purchase_repo import PurchaseRepository
from app.repo.discussion_repo import DiscussionRepository

from app.service.user_service import UserService
from app.service.app_service import AppService
from app.service.review_service import ReviewService
from app.service.purchase_service import PurchaseService
from app.service.discussion_service import DiscussionService

from app.core.logging import logger

oauth_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")


def skip_limit_params(
    skip: Annotated[int, Query(ge=0, lt=99)] = 0,
    limit: Annotated[int, Query(ge=0, lt=100)] = 10,
) -> tuple[int, int]:
    return skip, limit


async def get_current_user_id(token: TokenDep, redis: RedisDep) -> UUID | None:
    payload = await decode_access_token(token)
    logger.info(payload)
    user_id = payload.get("sub")

    if user_id is None:
        raise invalid_token_payload_exception

    return UUID(user_id)


async def get_current_user(
    token: TokenDep, user_service: UserServiceDep
) -> UserDB | None:
    payload = await decode_access_token(token)
    logger.info(payload)
    user_id = payload.get("sub")

    if user_id is None:
        raise invalid_token_payload_exception

    user = await user_service.get_user(id=UUID(user_id))

    return user


def require_role(role: UserRole) -> UserDB:
    def wrapper(user: UserDep) -> UserDB:
        if role not in user.roles:
            exception = no_rights_exception
            exception.detail = f"{exception.detail}. Role '{role}' required"
            raise no_rights_exception
        return user

    return wrapper


def _require_role(role: UserRole) -> UserDB:
    def wrapper(token: TokenDep, redis: RedisDep) -> UserDB:
        payload = decode_access_token(token, redis)
        user_roles = payload.get("role")
        user_id = payload.get("sub")

        if user_roles is None or user_id is None:
            raise invalid_token_payload_exception

        if role not in user_roles:
            raise no_rights_exception

        return user_id

    return wrapper


def get_user_repo(session: SessionDep) -> UserRepository:
    return UserRepository(session)


def get_user_service(user_repo: UserRepoDep) -> UserService:
    return UserService(user_repo)


def get_app_repo(session: SessionDep) -> AppRepository:
    return AppRepository(session)


def get_app_service(
    app_repo: AppRepoDep, user_service: UserServiceDep
) -> AppService:
    return AppService(app_repo, user_service)


def get_review_repo(
    app_repo: AppRepoDep, session: SessionDep
) -> ReviewRepository:
    return ReviewRepository(session)


def get_review_service(
    review_repo: ReviewRepoDep, app_service: AppServiceDep
) -> ReviewService:
    return ReviewService(review_repo, app_service)


def get_purchase_repo(session: SessionDep, app_repo: AppRepoDep) -> PurchaseRepository:
    return PurchaseRepository(session)


def get_purchase_service(
    redis: RedisDep,
    app_service: AppServiceDep, 
    purchase_repo: PurchaseRepoDep
) -> PurchaseService:
    return PurchaseService(redis, app_service, purchase_repo)


def get_discussion_repo(session: SessionDep) -> DiscussionRepository:
    return DiscussionRepository(session)


def get_discussion_service(
    discussion_repo: DiscussionRepoDep, app_service: AppServiceDep
) -> DiscussionService:
    return DiscussionService(discussion_repo, app_service)


SessionDep = Annotated[AsyncSession, Depends(get_session)]

UserIdDep = Annotated[UUID, Depends(get_current_user_id)]
UserDep = Annotated[UserDB, Depends(get_current_user)]
PublisherDep = Annotated[UserDB, Depends(require_role(UserRole.PUBLISHER))]

TokenDep = Annotated[str, Depends(oauth_scheme)]

SkipLimitParams = Annotated[tuple[int, int], Depends(skip_limit_params)]

UserServiceDep = Annotated[UserService, Depends(get_user_service)]
UserRepoDep = Annotated[UserRepository, Depends(get_user_repo)]

AppServiceDep = Annotated[AppService, Depends(get_app_service)]
AppRepoDep = Annotated[AppRepository, Depends(get_app_repo)]

ReviewServiceDep = Annotated[ReviewService, Depends(get_review_service)]
ReviewRepoDep = Annotated[ReviewRepository, Depends(get_review_repo)]

PurchaseServiceDep = Annotated[PurchaseService, Depends(get_purchase_service)]
PurchaseRepoDep = Annotated[PurchaseRepository, Depends(get_purchase_repo)]

DiscussionServiceDep = Annotated[
    DiscussionService, Depends(get_discussion_service)
]
DiscussionRepoDep = Annotated[
    DiscussionRepository, Depends(get_discussion_repo)
]

RedisDep = Annotated[Redis, Depends(get_redis)]

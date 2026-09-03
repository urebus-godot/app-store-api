from __future__ import annotations
from typing import Annotated, Optional
from uuid import UUID
from functools import lru_cache
import logging
import json

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import Depends, Query, Request, Response
from fastapi.security import OAuth2PasswordBearer
 
from app.db.postgres import get_session, session_factory
from app.db.redis import get_redis

from app.core.exceptions import (
    no_rights_exception,
    invalid_token_payload_exception,
    too_many_requests_exception,
    app_not_purchased_exception,
    token_expired_exception,
    invalid_access_token_exception,
    incorrect_password_exception,
    InvalidTokenPayloadError,
    TokenError,
    TokenExpiredError,
    InvalidTokenError
)
from app.core.auth import decode_access_token
from app.core.config import settings

from app.schemas.token import TokenData
from app.models.user import UserDB, UserRole

from app.db.rate_limiter import RateLimiter
from app.uow.orm import OrmUnitOfWork

from app.repo.user_repo import UserRepository
from app.repo.finance_repo import FinanceRepository
from app.repo.app_repo import AppRepository
from app.repo.review_repo import ReviewRepository
from app.repo.purchase_repo import PurchaseRepository
from app.repo.discussion_repo import DiscussionRepository

from app.services.finance_service import FinanceService
from app.services.user_service import UserService
from app.services.app_service import AppService
from app.services.review_service import ReviewService
from app.services.purchase_service import PurchaseService
from app.services.discussion_service import DiscussionService
from app.services.app_archive_service import AppArchiveService
from app.services.media_service import MediaService

from app.storage.minio_repo import MinioStorage
from app.storage.protocol import ObjectStorage

from app.ws.discussion_manager import (
    DiscussionWebsocketManager
)

oauth_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")
optional_oauth_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/users/login",
    auto_error=False
)

token_errors = {
    InvalidTokenPayloadError: invalid_token_payload_exception,
    TokenExpiredError: token_expired_exception,
    InvalidTokenError: invalid_access_token_exception
}

logger = logging.getLogger("api.deps")


def skip_limit_params(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(gt=0, le=100)] = 10,
) -> tuple[int, int]:
    return skip, limit


def get_refresh_secret_key() -> str:
    return settings.REFRESH_SECRET_KEY


def get_access_secret_key() -> str:
    return settings.ACCESS_SECRET_KEY


def validate_access_token(
    token: str, 
    secret_key: str
) -> TokenData:
    payload = decode_access_token(token, secret_key)
    user_id = payload.get("sub")
    roles = payload.get("roles")
    logger.info(f"{type(roles)}; roles={roles}")

    if user_id is None or not roles:
        raise InvalidTokenPayloadError()

    return TokenData(
        user_id=UUID(user_id), roles=json.loads(roles)
    )


def get_current_user_id_optionally(
    token: Annotated[Optional[str], Depends(optional_oauth_scheme)], 
    secret_key: AccessSecretKeyDep
) -> Optional[UUID]:
    try:
        payload = decode_access_token(token, secret_key)
        user_id = payload.get("sub")

        if user_id is None:
            raise invalid_token_payload_exception

        return UUID(user_id)

    except Exception:
        return None


def get_current_user_id(
    token: TokenDep, secret_key: AccessSecretKeyDep
) -> UUID:
    try:
        token_data = validate_access_token(token, secret_key)
        return token_data.user_id
    except TokenError as e:
        raise token_errors[type(e)]


async def get_current_user(
    token: TokenDep, 
    user_service: UserServiceDep,
    secret_key: AccessSecretKeyDep
) -> UserDB | None:
    try:
        token_data = validate_access_token(token, secret_key)
        return await user_service.get_user_by_id(token_data.user_id)
    except TokenError as e:
        raise token_errors[type(e)] #invalid_token_payload_exception


async def user_purchased_app(app_id: UUID, user: UserDep) -> None:
    purchased_apps_ids = (app.id for app in user.purchased_apps)
    if app_id not in purchased_apps_ids:
        raise app_not_purchased_exception


def get_rate_limiter(redis: RedisDep) -> RateLimiter:
    return RateLimiter(redis)


async def rate_limit(
    rate_limiter: Annotated[RateLimiter, Depends(get_rate_limiter)],
    request: Request,
    response: Response,
    user_id: Optional[UUID] = Depends(get_current_user_id_optionally),
):
    # 1. Грубый лимит по IP — защита от анонимного флуда
    ip_result = await rate_limiter.check(
        request.client.host,
        scope="ip",
        limit= 15,
        window_seconds=60,
    )
    response.headers["X-RateLimit-Remaining-IP-Address"] = (
        str(ip_result.remaining_requests))
    if not ip_result.allowed:
        raise too_many_requests_exception

    # 2. Более узкий лимит по user_id — только для авторизованных
    if user_id is not None:
        user_result = await rate_limiter.check(
            user_id,
            scope="user",
            limit=20,
            window_seconds=60,
        )
        response.headers["X-RateLimit-Remaining-User"] = (
            str(user_result.remaining_requests))
        if not user_result.allowed:
            raise too_many_requests_exception

 
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return session_factory


def require_role(role: UserRole) -> UserDB:
    def wrapper(
        token: TokenDep, secret_key: AccessSecretKeyDep
    ) -> UserDB:
        try:
            token_data = validate_access_token(token, secret_key)
            user_roles = token_data.roles
            user_id = token_data.user_id

            if role.value not in user_roles:
                raise no_rights_exception
        except TokenError as e:
            raise token_errors[type(e)]
        return user_id
    return wrapper


def get_admin_password() -> str:
    return settings.ADMIN_PASSWORD


def check_admin_password(
    password: str,
    admin_password: Annotated[str, Depends(get_admin_password)]
) -> None:
    if password != admin_password:
        raise incorrect_password_exception


def can_send_email() -> bool:
    return True


def get_user_repo(session: SessionDep) -> UserRepository:
    return UserRepository(session)

def get_user_service(
    app_service: AppServiceDep,
    uow: UnitOfWorkDep,
    storage: ObjectStorageDep
) -> UserService:
    return UserService(app_service=app_service, uow=uow, storage=storage)


def get_finance_repo(session: SessionDep) -> FinanceRepository:
    return FinanceRepository(session)

def get_finance_service(
    uow: UnitOfWorkDep
) -> FinanceService:
    return FinanceService(uow)


def get_app_repo(session: SessionDep) -> AppRepository:
    return AppRepository(session)

def get_app_service(
    uow: UnitOfWorkDep,
    storage: ObjectStorageDep,
    media_service: MediaServiceDep
) -> AppService:
    return AppService(
        uow=uow, 
        storage=storage,
        media_service=media_service
    )


def get_review_repo(
    session: SessionDep
) -> ReviewRepository:
    return ReviewRepository(session)

def get_review_service(
    app_service: AppServiceDep,
    uow: UnitOfWorkDep
) -> ReviewService:
    return ReviewService(app_service, uow)


def get_purchase_repo(
    session: SessionDep
) -> PurchaseRepository:
    return PurchaseRepository(session)

def get_purchase_service(
    redis: RedisDep, 
    app_service: AppServiceDep, 
    user_service: UserServiceDep,
    uow: UnitOfWorkDep
) -> PurchaseService:
    return PurchaseService(
        redis, app_service, user_service, uow
    )


def get_discussion_repo(session: SessionDep) -> DiscussionRepository:
    return DiscussionRepository(session)

def get_discussion_service(
    app_service: AppServiceDep,
    uow: UnitOfWorkDep
) -> DiscussionService:
    return DiscussionService(app_service, uow)

def get_discussion_manager(redis: RedisDep) -> DiscussionWebsocketManager:
    return DiscussionWebsocketManager(redis)


async def get_unit_of_work(
    session_factory: SessionFactoryDep
) -> OrmUnitOfWork:
    return OrmUnitOfWork(session_factory)


@lru_cache
def get_object_storage() -> ObjectStorage:
    return MinioStorage()


def get_app_archive_service(
    uow: UnitOfWorkDep,
    storage: ObjectStorageDep
) -> AppArchiveService:
    return AppArchiveService(storage=storage, uow=uow)


def get_media_service(
    uow: UnitOfWorkDep, 
    storage: ObjectStorageDep
) -> MediaService:
    return MediaService(storage=storage, uow=uow)


def get_finance_api_client():
    from app.main import app
    return app.state.finance_api_client


SessionDep = Annotated[AsyncSession, Depends(get_session)]
SessionFactoryDep = Annotated[AsyncSession, Depends(get_session_factory)]

UserIdDep = Annotated[UUID, Depends(get_current_user_id)]
UserDep = Annotated[UserDB, Depends(get_current_user)]
PublisherDep = Annotated[UserDB, Depends(require_role(UserRole.PUBLISHER))]
AdminDep = Annotated[UserDB, Depends(require_role(UserRole.ADMIN))]

TokenDep = Annotated[str, Depends(oauth_scheme)]

SkipLimitParams = Annotated[tuple[int, int], Depends(skip_limit_params)]

UserServiceDep = Annotated[UserService, Depends(get_user_service)]
UserRepoDep = Annotated[UserRepository, Depends(get_user_repo)]

FinanceServiceDep = Annotated[FinanceService, Depends(get_finance_service)]
FinanceRepoDep = Annotated[FinanceRepository, Depends(get_finance_repo)]

AppServiceDep = Annotated[AppService, Depends(get_app_service)]
AppRepoDep = Annotated[AppRepository, Depends(get_app_repo)]

ReviewServiceDep = Annotated[ReviewService, Depends(get_review_service)]
ReviewRepoDep = Annotated[ReviewRepository, Depends(get_review_repo)]

PurchaseServiceDep = Annotated[PurchaseService, Depends(get_purchase_service)]
PurchaseRepoDep = Annotated[PurchaseRepository, Depends(get_purchase_repo)]

AppArchiveServiceDep = Annotated[
    AppArchiveService, Depends(get_app_archive_service)
    ]
MediaServiceDep = Annotated[MediaService, Depends(get_media_service)]

UnitOfWorkDep = Annotated[OrmUnitOfWork, Depends(get_unit_of_work)]

DiscussionServiceDep = Annotated[
    DiscussionService, Depends(get_discussion_service)
]
DiscussionRepoDep = Annotated[
    DiscussionRepository, Depends(get_discussion_repo)
]

DiscussionManagerDep = Annotated[
    DiscussionWebsocketManager, Depends(get_discussion_manager)
]

ObjectStorageDep = Annotated[
    ObjectStorage, Depends(get_object_storage)
]

RedisDep = Annotated[Redis, Depends(get_redis)]

SendEmailDep = Annotated[
    bool, Depends(can_send_email)
]

RefreshSecretKeyDep = Annotated[str, Depends(get_refresh_secret_key)]
AccessSecretKeyDep = Annotated[str, Depends(get_access_secret_key)]
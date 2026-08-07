from __future__ import annotations
from typing import Annotated, Optional
from uuid import UUID
from functools import lru_cache

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
    app_not_purchased_exception
)
from app.dependencies.rate_limiter import RateLimiter
from app.core.auth import decode_access_token
from app.core.config import settings
from app.models.user import UserDB, UserRole

from app.uow.orm import OrmUnitOfWork

from app.repo.user_repo import UserRepository
from app.repo.finance_repo import FinanceRepository
from app.repo.app_repo import AppRepository
from app.repo.review_repo import ReviewRepository
from app.repo.purchase_repo import PurchaseRepository
from app.repo.discussion_repo import DiscussionRepository

from app.service.finance_service import FinanceService
from app.service.user_service import UserService
from app.service.app_service import AppService
from app.service.review_service import ReviewService
from app.service.purchase_service import PurchaseService
from app.service.discussion_service import DiscussionService
from app.service.app_archive_service import AppArchiveService
from app.service.media_service import MediaService

from app.core.logging import logger

from app.storage.minio_repository import MinioStorage
from app.storage.protocols import ObjectStorage

oauth_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")
oauth_scheme_2 = OAuth2PasswordBearer(
    tokenUrl="/api/v1/users/login", auto_error=False
    )


def skip_limit_params(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(gt=0, le=100)] = 10,
) -> tuple[int, int]:
    return skip, limit


def get_refresh_secret_key() -> str:
    return settings.REFREH_SECRET_KEY


def get_access_secret_key() -> str:
    return settings.ACCESS_SECRET_KEY


def get_current_user_id_optionally(
    token: Annotated[Optional[str], Depends(oauth_scheme_2)], 
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
    payload = decode_access_token(token, secret_key)
    logger.info(payload)
    user_id = payload.get("sub")

    if user_id is None:
        raise invalid_token_payload_exception

    return UUID(user_id)


async def get_current_user(
    token: TokenDep, 
    user_service: UserServiceDep,
    secret_key: AccessSecretKeyDep
) -> UserDB | None:
    payload = decode_access_token(token, secret_key)
    logger.info(payload)
    user_id = payload.get("sub")

    if user_id is None:
        raise invalid_token_payload_exception

    user = await user_service.get_user_by_id(UUID(user_id))

    return user


async def user_purchased_app(app_id: UUID, user: UserDep) -> None:
    purchased_apps_ids = (app.id for app in user.purchased_apps)
    if app_id not in purchased_apps_ids:
        raise app_not_purchased_exception


def get_rate_limiter(redis: RedisDep) -> RateLimiter:
    return RateLimiter(redis)


async def rate_limit(
    rate_limiter: Annotated[RateLimiter, Depends(get_rate_limiter)],
    user_id: Annotated[
        Optional[UUID], Depends(get_current_user_id_optionally)
        ],
    request: Request,
    response: Response
):
    logger.info("Start checking for limit")
    if user_id is not None:
        result = await rate_limiter.check(user_id)
        logger.info("Checked for authenticated user")
    else:
        result = await rate_limiter.check(request.client.host)
        logger.info("Checked for guest")

    response.headers["X-RateLimit-Remaining"] = str(result.remaining_requests)

    if not result.allowed:
        logger.info("Request limit exceeded")
        raise too_many_requests_exception


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return session_factory


def require_role(role: UserRole) -> UserDB:
    def wrapper(user: UserDep) -> UserDB:
        if role not in user.roles:
            exception = no_rights_exception
            exception.detail = f"{exception.detail}. Role '{role}' required"
            raise no_rights_exception
        return user

    return wrapper


def _require_role(role: UserRole) -> UserDB:
    def wrapper(
        token: TokenDep, redis: RedisDep, secret_key: AccessSecretKeyDep
        ) -> UserDB:
        payload = decode_access_token(token, secret_key)
        user_roles = payload.get("role")
        user_id = payload.get("sub")

        if user_roles is None or user_id is None:
            raise invalid_token_payload_exception

        if role not in user_roles:
            raise no_rights_exception

        return user_id

    return wrapper


def can_send_email() -> bool:
    return True


def get_user_repo(session: SessionDep) -> UserRepository:
    return UserRepository(session)

def get_user_service(
    user_repo: UserRepoDep,
    app_service: AppServiceDep,
    uow: UnitOfWorkDep
) -> UserService:
    return UserService(user_repo, app_service, uow)


def get_finance_repo(session: SessionDep) -> FinanceRepository:
    return FinanceRepository(session)

def get_finance_service(
    finance_repo: FinanceRepoDep,
    user_repo: UserRepoDep,
    uow: UnitOfWorkDep
) -> FinanceService:
    return FinanceService(finance_repo, user_repo, uow)


def get_app_repo(session: SessionDep) -> AppRepository:
    return AppRepository(session)

def get_app_service(
    app_repo: AppRepoDep, 
    user_repo: UserRepoDep,
    purchase_repo: PurchaseRepoDep,
    uow: UnitOfWorkDep
) -> AppService:
    return AppService(app_repo, user_repo, purchase_repo, uow)


def get_review_repo(
    session: SessionDep
) -> ReviewRepository:
    return ReviewRepository(session)

def get_review_service(
    review_repo: ReviewRepoDep, 
    app_service: AppServiceDep,
    uow: UnitOfWorkDep
) -> ReviewService:
    return ReviewService(review_repo, app_service, uow)


def get_purchase_repo(
    session: SessionDep
) -> PurchaseRepository:
    return PurchaseRepository(session)

def get_purchase_service(
    redis: RedisDep, 
    app_service: AppServiceDep, 
    user_service: UserServiceDep,
    purchase_repo: PurchaseRepoDep,
    uow: UnitOfWorkDep
) -> PurchaseService:
    return PurchaseService(
        redis, app_service, user_service, purchase_repo, uow
        )


def get_discussion_repo(session: SessionDep) -> DiscussionRepository:
    return DiscussionRepository(session)

def get_discussion_service(
    discussion_repo: DiscussionRepoDep, 
    app_service: AppServiceDep,
    uow: UnitOfWorkDep
) -> DiscussionService:
    return DiscussionService(discussion_repo, app_service, uow)


async def get_unit_of_work(
    session_factory: SessionFactoryDep
) -> OrmUnitOfWork:
    return OrmUnitOfWork(session_factory)


@lru_cache
def get_object_storage() -> ObjectStorage:
    # MinioStorage не держит постоянного соединения (клиент создаётся
    # внутри каждого метода через async with), поэтому его безопасно
    # переиспользовать как синглтон на всё приложение.
    return MinioStorage()


def get_app_archive_service(
    uow: UnitOfWorkDep,
    storage: Annotated[ObjectStorage, Depends(get_object_storage)]
) -> AppArchiveService:
    return AppArchiveService(storage=storage, uow=uow)


def get_media_service(
    uow: UnitOfWorkDep, 
    storage: ObjectStorage = Depends(get_object_storage),
) -> MediaService:
    return MediaService(storage=storage, uow=uow)


SessionDep = Annotated[AsyncSession, Depends(get_session)]
SessionFactoryDep = Annotated[AsyncSession, Depends(get_session_factory)]

UserIdDep = Annotated[UUID, Depends(get_current_user_id)]
UserDep = Annotated[UserDB, Depends(get_current_user)]
PublisherDep = Annotated[UserDB, Depends(require_role(UserRole.PUBLISHER))]

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

RedisDep = Annotated[Redis, Depends(get_redis)]

SendEmailDep = Annotated[
    bool, Depends(can_send_email)
]

RefreshSecretKeyDep = Annotated[str, Depends(get_refresh_secret_key)]
AccessSecretKeyDep = Annotated[str, Depends(get_access_secret_key)]
from typing import Optional, Union
from uuid import UUID
import logging

from fastapi import (
    APIRouter, 
    status, 
    Depends, 
    Query
)

from app.api.deps import (
    UserIdDep,
    SkipLimitParams,
    PublisherDep,
    AppServiceDep,
    rate_limit
)
from app.utils.search import SearchQuery
from app.base_models.app import (
    GameGenre
)
from app.schemas.app import (
    AppRequest,
    AppUpdate,
    GameUpdate,
    AppResponse,
    GameRequest,
    GameResponse,
    AppResponseWithPublisher,
    GameResponseWithPublisher,
)

router = APIRouter(
    dependencies=[Depends(rate_limit)]
)

logger = logging.getLogger("app.app_router")


@router.post(
    "/apps", 
    status_code=status.HTTP_201_CREATED,
    response_model=AppResponse
)
async def upload_app(
    data: AppRequest,
    publisher_id: PublisherDep,
    app_service: AppServiceDep
) -> AppResponse:
    """Создаёт приложение в базе данных.
    
    **Возвращает**: AppResponse"""
    app = await app_service.create_app(data, publisher_id)
    return app


@router.post(
    "/games", 
    status_code=status.HTTP_201_CREATED,
    response_model=GameResponse
)
async def upload_game(
    data: GameRequest,
    publisher_id: PublisherDep,
    app_service: AppServiceDep
) -> GameResponse:
    """Создаёт игру в базе данных.
    
    **Возвращает**: GameResponse"""
    game = await app_service.create_app(data, publisher_id)
    return game


@router.patch(
    "/apps/{id}",
    response_model=AppResponse
)
async def update_app(
    id: UUID,
    data: AppUpdate,
    user_id: UserIdDep,
    app_service: AppServiceDep
) -> AppResponse:
    """Обновляет атрибуты приложения 
    (если его категория равна "application").
    
    **Возвращает**: AppResponse"""
    app = await app_service.update_app(
        data=data, id=id, user_id=user_id
    )
    return app


@router.patch(
    "/games/{id}",
    response_model=GameResponse
)
async def update_game(
    id: UUID,
    data: GameUpdate,
    user_id: UserIdDep,
    app_service: AppServiceDep
) -> GameResponse:
    """Обновляет атрибуты игры.
    
    **Возвращает**: GameResponse"""
    app = await app_service.update_app(
        data=data, id=id, user_id=user_id
    )
    return app


@router.get(
    "/apps/{id}",
    response_model=Union[AppResponseWithPublisher | GameResponseWithPublisher]
)
async def get_app(
    id: UUID, app_service: AppServiceDep
) -> AppResponseWithPublisher | GameResponseWithPublisher:
    """Находит приложение по id в базе данных.
    
    **Возвращает**: AppResponseWithPublisher или GameResponseWithPublisher"""
    logger.info("get_app")
    app = await app_service.get_app(id)
    return app


@router.get(
    "/apps",
    response_model=list[AppResponseWithPublisher]
)
async def get_apps(
    skip_limit: SkipLimitParams,
    app_service: AppServiceDep,
    search_query: Optional[SearchQuery] = None,
) -> list[AppResponseWithPublisher]:
    """Находит приложения в базе данных.

    **Параметры**: *search_query* - если указан,
    приложения фильтруются по совпадающим ключевым словам
    
    **Возвращает**: list[AppResponseWithPublisher]"""
    skip, limit = skip_limit
    apps = await app_service.get_apps(
        search_query=search_query, skip=skip, limit=limit
    )
    return apps


@router.get(
    "/games",
    response_model=list[GameResponseWithPublisher]
)
async def get_games(
    skip_limit: SkipLimitParams,
    app_service: AppServiceDep,
    search_query: Optional[SearchQuery] = None
) -> list[GameResponseWithPublisher]:
    """Находит игры в базе данных.

    **Параметры**: *search_query* - если указан,
    игры фильтруются по совпадающим ключевым словам
    
    **Возвращает**: list[GameResponseWithPublisher]"""
    skip, limit = skip_limit
    games = await app_service.get_games(
        search_query=search_query, skip=skip, limit=limit
    )
    return games


@router.get(
    "/games/with_genre",
    response_model=list[GameResponseWithPublisher]
)
async def get_games_with_genre(
    skip_limit: SkipLimitParams,
    app_service: AppServiceDep,
    search_query: Optional[SearchQuery] = None,
    genre: Optional[GameGenre] = None,
) -> list[GameResponseWithPublisher]:
    """Находит игры в базе данных.

    **Параметры**: *search_query* - если указан,
    игры фильтруются по совпадающим ключевым словам
    
    **Возвращает**: list[GameResponseWithPublisher]"""
    skip, limit = skip_limit
    games = await app_service.get_games_with_genre(
        search_query=search_query, genre=genre, skip=skip, limit=limit
    )
    return games


@router.get(
    "/games/top",
    response_model=list[GameResponseWithPublisher]
)
async def get_top_games(
    app_service: AppServiceDep,
    skip_limit: SkipLimitParams,
    genre: Optional[GameGenre] = Query(default=None)
) -> list[GameResponseWithPublisher]:
    """Находит игры в базе данных, 
    отсортированные по количеству покупок, рейтингу в порядке убывания.

    **Параметры**: *genre* - если указан,
    игры фильтруются по совпадающему жанру
    
    **Возвращает**: GameResponseWithPublisher"""
    if genre is None:
        games = await app_service.get_top_games(*skip_limit)
    else:
        games = await app_service.get_top_games_genre(genre, *skip_limit)
    return games


@router.get(
    "/apps/purchased/me",
    response_model=list[AppResponse | GameResponse]
)
async def get_purchased_apps(
    user_id: UserIdDep,
    skip_limit: SkipLimitParams,
    app_service: AppServiceDep,
) -> list[AppResponse | GameResponse]:
    """Находит приложения в базе данных, 
    приобретённые пользователем.
    
    **Возвращает**: list[AppResponse | GameResponse]"""
    apps = await app_service.get_purchased_apps(
        user_id, *skip_limit
    )
    return apps


@router.get(
    "/apps/published/me",
    response_model=list[AppResponse | GameResponse]
)
async def get_own_published_apps(
    user_id: UserIdDep,
    skip_limit: SkipLimitParams,
    app_service: AppServiceDep,
) -> list[AppResponse | GameResponse]:
    """Находит приложения в базе данных, 
    опубликованные пользователем.
    
    **Возвращает**: list[AppResponse | GameResponse]"""
    skip, limit = skip_limit
    apps = await app_service.get_publisher_apps(
        skip=skip, limit=limit, user_id=user_id, public_only=False
    )
    return apps


@router.get(
    "/apps/published/{user_id}",
    response_model=list[AppResponse | GameResponse]
)
async def get_publisher_apps(
    user_id: UUID,
    skip_limit: SkipLimitParams,
    app_service: AppServiceDep
) -> list[AppResponse | GameResponse]:
    """Находит приложения в базе данных, 
    опубликованные пользователем с указанным *user_id*.
    
    **Возвращает**: list[AppResponse | GameResponse]"""
    skip, limit = skip_limit
    apps = await app_service.get_publisher_apps(
        skip=skip, limit=limit, user_id=user_id
    )
    return apps


@router.delete(
    "/apps/{id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_app(
    id: UUID, 
    user_id: UserIdDep, 
    app_service: AppServiceDep
) -> None:
    """Удаляет приложение с указанным *id*
    и связанные с ним файлы в MinIO.
    
    **Возвращает**: None"""
    await app_service.delete_app(
        id=id, user_id=user_id
    )

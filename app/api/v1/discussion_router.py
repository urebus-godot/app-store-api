from uuid import UUID

from fastapi import APIRouter, status

from app.models.discussion import (
    DiscussionRequest,
    DiscussionResponse,
    ShortDiscussionResponse,
    MessageRequest,
    MessageResponse,
)
from app.dependencies import DiscussionServiceDep, UserIdDep, UnitOfWorkDep

router = APIRouter()


# ------ Discussion routes ------

@router.post(
    "/discussions/{app_id}", 
    status_code=status.HTTP_201_CREATED
    )
async def create_discussion(
    data: DiscussionRequest,
    app_id: UUID,
    user_id: UserIdDep,
    discussion_service: DiscussionServiceDep,
    uow: UnitOfWorkDep
) -> DiscussionResponse:
    return await discussion_service.create_discussion(
        data, user_id, app_id, uow
        )


@router.get("/discussions/{id}")
async def get_discussion(
    id: UUID, discussion_service: DiscussionServiceDep
) -> DiscussionResponse:
    return await discussion_service.get_discussion(id)


@router.get("/discussions/app/{app_id}")
async def get_app_discussions(
    app_id: UUID, discussion_service: DiscussionServiceDep
) -> list[ShortDiscussionResponse]:
    return await discussion_service.get_app_discussions(app_id)


@router.get("/discussions/user/me")
async def get_my_discussions(
    user_id: UserIdDep, 
    discussion_service: DiscussionServiceDep
) -> list[ShortDiscussionResponse]:
    return await discussion_service.get_user_discussions(user_id)


@router.delete(
    "/discussions/{id}",
    status_code=status.HTTP_204_NO_CONTENT
    )
async def delete_discussion(
    id: UUID, 
    user_id: UserIdDep, 
    discussion_service: DiscussionServiceDep,
    uow: UnitOfWorkDep
) -> None:
    await discussion_service.delete_discussion(id, user_id, uow)


# ------ Message routes ------

@router.post(
    "/discussions/{discussion_id}/messages",
    status_code=status.HTTP_201_CREATED,
)
async def create_message(
    data: MessageRequest,
    discussion_id: UUID,
    user_id: UserIdDep,
    discussion_service: DiscussionServiceDep,
    uow: UnitOfWorkDep
) -> MessageResponse:
    return await discussion_service.create_message(
        data, user_id, discussion_id, uow
    )


@router.delete(
    "/discussions/messages/{id}", 
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_message(
    id: UUID, 
    user_id: UserIdDep, 
    discussion_service: DiscussionServiceDep,
    uow: UnitOfWorkDep
) -> None:
    await discussion_service.delete_message(id, user_id, uow)

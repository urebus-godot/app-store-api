from uuid import UUID

from fastapi import APIRouter, status

from app.models.discussion import (
    DiscussionResponse, DiscussionRequest,
    MessageRequest, MessageResponse
    )
from app.dependencies import DiscussionServiceDep, UserIdDep

router = APIRouter()

# ------ Discussion routes ------

@router.post(
    "/apps/{app_id}/discussions", status_code=status.HTTP_201_CREATED
    )
async def create_discussion(
    data: DiscussionRequest,
    user_id: UserIdDep,
    discussion_service: DiscussionServiceDep
) -> DiscussionResponse:
    return await discussion_service.create_discussion(data, user_id)


@router.get("/apps/discussions/{id}")
async def get_discussion(
    id: UUID,
    discussion_service: DiscussionServiceDep
) -> DiscussionResponse:
    return await discussion_service.get_discussion(id)


@router.delete("/apps/discussions/{id}")
async def delete_discussion(
    id: UUID,
    user_id: UserIdDep,
    discussion_service: DiscussionServiceDep
) -> dict[str, str]:
    return await discussion_service.delete_discussion(id)


# ------ Message routes ------

@router.post(
    "/apps/discussions/{discussion_id}/create-message", 
    status_code=status.HTTP_201_CREATED
    )
async def create_message(
    discussion_id: UUID,
    data: MessageRequest,
    user_id: UserIdDep,
    discussion_service: DiscussionServiceDep
) -> MessageResponse:
    return await discussion_service.create_message(
        data, user_id, discussion_id
        )


@router.delete("/apps/discussions/messages/{id}")
async def delete_message(
    id: UUID,
    user_id: UserIdDep,
    discussion_service: DiscussionServiceDep
) -> dict[str, str]:
    return await discussion_service.delete_message(id, user_id)
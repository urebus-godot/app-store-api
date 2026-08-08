from uuid import UUID
import asyncio

from fastapi import APIRouter, status, Depends, WebSocket
from fastapi.exceptions import WebSocketException

from app.core.config import settings
from app.core.exceptions import InvalidTokenError, InvalidTokenPayloadError
from app.core.logging import logger

from app.schemas.discussion import (
    DiscussionRequest,
    DiscussionResponse,
    ShortDiscussionResponse,
    MessageRequest,
    MessageResponse
)
from app.api.dependencies import (
    DiscussionServiceDep, 
    UserIdDep,
    rate_limit, 
    SkipLimitParams, 
    DiscussionManagerDep,
    validate_access_token,
    AccessSecretKeyDep,
    UserServiceDep
)

router = APIRouter(
    dependencies=[Depends(rate_limit)]
    )


# ------ Discussion routes ------

@router.post(
    "/discussions/{app_id}", 
    status_code=status.HTTP_201_CREATED
)
async def create_discussion(
    data: DiscussionRequest,
    app_id: UUID,
    user_id: UserIdDep,
    discussion_service: DiscussionServiceDep
) -> ShortDiscussionResponse:
    return await discussion_service.create_discussion(
        data, user_id, app_id
    )


@router.get("/discussions/{id}")
async def get_discussion(
    id: UUID, 
    skip_limit: SkipLimitParams,
    discussion_service: DiscussionServiceDep
) -> DiscussionResponse:
    skip, limit = skip_limit
    return await discussion_service.get_discussion(
        id=id, skip=skip, limit=limit
        )


@router.websocket("/ws/discussions/{id}")
async def ws_discussion(
    id: UUID,
    websocket: WebSocket, 
    discussion_service: DiscussionServiceDep,
    user_service: UserServiceDep,
    discussion_manager: DiscussionManagerDep,
    secret_key: AccessSecretKeyDep
):
    await websocket.accept()
    try:
        logger.info("Awaiting data from websocket...")
        ws_data = asyncio.wait_for(
            websocket.receive_json(), 
            timeout=settings.AUTH_TIMEOUT
            )
        user_id = await validate_access_token(ws_data["token"], secret_key)
        user = await user_service.get_user_by_id(user_id)
        logger.info("Validated token from user")
    except asyncio.TimeoutError:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Authentication timeout"
        )
        return
    except (InvalidTokenError, InvalidTokenPayloadError):
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Invalid token"
        )
        return

    discussion = await discussion_service.get_discussion(id)

    if discussion is None:
        await websocket.close(
            code=status.WS_1003_UNSUPPORTED_DATA,
            reason="Discussion not found"
        )
        return

    await websocket.send_json({"type": "auth_ok"})
    await discussion_manager.connect(id, websocket)

    msg = {
        "message": 
        f"User {user.username} connected to the discussion"
    }
    await discussion_manager.publish(id, msg)

    try:
        while True:
            raw_data = await websocket.receive_json()
            message_data = MessageRequest(**raw_data)
            message = await discussion_service.create_message(
                data=message_data, 
                author_id=user_id, 
                discussion_id=id
            )
            response = (
                MessageResponse
                .model_validate(message)
                .model_dump_json()
                )
            await discussion_manager.publish(id, response)
    except WebSocketException:
        msg = {
            "message": 
            f"User {user.username} disconnected from the discussion"
            }
        await discussion_manager.publish(id, msg)
    finally:
        await discussion_manager.disconnect(id, websocket)


@router.get("/discussions/app/{app_id}")
async def get_app_discussions(
    app_id: UUID, discussion_service: DiscussionServiceDep
) -> list[ShortDiscussionResponse]:
    return await discussion_service.get_app_discussions(app_id)


@router.get("/discussions/user/me")
async def get_my_discussions(
    user_id: UserIdDep, discussion_service: DiscussionServiceDep
) -> list[ShortDiscussionResponse]:
    return await discussion_service.get_user_discussions(user_id)


@router.delete(
    "/discussions/{id}", 
    status_code=status.HTTP_204_NO_CONTENT
    )
async def delete_discussion(
    id: UUID,
    user_id: UserIdDep,
    discussion_service: DiscussionServiceDep
) -> None:
    await discussion_service.delete_discussion(id, user_id)


# ------ Message routes ------

@router.post(
    "/discussions/{discussion_id}/messages",
    status_code=status.HTTP_201_CREATED,
)
async def create_message(
    data: MessageRequest,
    discussion_id: UUID,
    user_id: UserIdDep,
    discussion_service: DiscussionServiceDep
) -> MessageResponse:
    return await discussion_service.create_message(
        data, user_id, discussion_id
    )


@router.delete(
    "/discussions/messages/{id}", 
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_message(
    id: UUID,
    user_id: UserIdDep,
    discussion_service: DiscussionServiceDep
) -> None:
    await discussion_service.delete_message(id, user_id)

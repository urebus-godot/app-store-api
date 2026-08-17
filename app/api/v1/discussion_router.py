from uuid import UUID
import asyncio
import logging
import json

from fastapi import APIRouter, status, Depends, WebSocket
from fastapi.websockets import WebSocketDisconnect

from pydantic import ValidationError

from app.core.config import settings
from app.core.exceptions import (
    InvalidTokenError, 
    InvalidTokenPayloadError, 
    UserNotFoundError
)
from app.schemas.discussion import (
    DiscussionRequest,
    DiscussionResponse,
    ShortDiscussionResponse,
    MessageRequest,
    MessageResponse
)
from app.schemas.ws_messages import incoming_adapter, AuthMessage
from app.schemas.ws_events import (
    ErrorEvent
)

from app.api.dependencies import (
    DiscussionServiceDep, 
    UserIdDep,
    rate_limit, 
    SkipLimitParams, 
    DiscussionManagerDep,
    validate_access_token,
    AccessSecretKeyDep,
    UserRepoDep,
    DiscussionRepoDep
)

router = APIRouter(
    dependencies=[Depends(rate_limit)]
)

logger = logging.getLogger("app.discussion_router")


# ------ Discussion routes ------

@router.websocket("/ws/discussions/{id}")
async def ws_discussion(
    id: UUID,
    websocket: WebSocket, 
    discussion_repo: DiscussionRepoDep,
    discussion_service: DiscussionServiceDep,
    user_repo: UserRepoDep,
    discussion_manager: DiscussionManagerDep,
    secret_key: AccessSecretKeyDep
):
    await websocket.accept()
    try:
        logger.info("Awaiting data from websocket...")
        ws_data = await asyncio.wait_for(
            websocket.receive_json(), 
            timeout=settings.AUTH_TIMEOUT
        )
        msg_type = ws_data.get("type", None)

        if msg_type is None or msg_type != "auth":
            await websocket.send_json(
                ErrorEvent(detail="Invalid message").model_dump(mode="json")
            )
            return
        
        user_id = validate_access_token(ws_data["token"], secret_key).user_id
        user = await user_repo.get_user_by_id(user_id)

        if not user:
            raise UserNotFoundError()

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
    except UserNotFoundError:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="User not found"
        )
        return
    except ValidationError as e:
        await websocket.send_json(
            ErrorEvent(detail=str(e)).model_dump(mode="json")
        )

    logger.info("Start getting discussion")
    discussion = await discussion_repo.get_discussion(id)
    
    if discussion is None:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Discussion not found"
        )
        return
    
    logger.info("Start connecting ws in the manager")
    await websocket.send_json({"type": "auth_ok"})
    await discussion_manager.connect(id, websocket)
    logger.info("Connected ws in the manager")

    try:
        while True:
            logger.info("Start message exchange")
            raw_data = await websocket.receive_json()
            try:
                msg = incoming_adapter.validate_python(raw_data)
            except ValidationError as e:
                await websocket.send_json(
                    ErrorEvent(detail=str(e)).model_dump(mode="json")
                )
                continue
            await discussion_service.handle_incoming_message(
                msg=msg, 
                discussion_manager=discussion_manager,
                user_id=user_id,
                discussion_id=id
            )
            logger.info("Published message")
            
    except WebSocketDisconnect:
        pass
    finally:
        await discussion_manager.disconnect(id, websocket)


@router.post(
    "/discussions/{app_id}", 
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit)]
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


@router.get(
    "/discussions/{id}",
    dependencies=[Depends(rate_limit)]
    )
async def get_discussion(
    id: UUID, 
    skip_limit: SkipLimitParams,
    discussion_service: DiscussionServiceDep
) -> DiscussionResponse:
    skip, limit = skip_limit
    return await discussion_service.get_discussion(
        id=id, skip=skip, limit=limit
    )


@router.get(
    "/discussions/app/{app_id}",
    dependencies=[Depends(rate_limit)]
)
async def get_app_discussions(
    app_id: UUID, discussion_service: DiscussionServiceDep
) -> list[ShortDiscussionResponse]:
    return await discussion_service.get_app_discussions(app_id)


@router.get(
    "/discussions/user/me",
    dependencies=[Depends(rate_limit)]
)
async def get_my_discussions(
    user_id: UserIdDep, discussion_service: DiscussionServiceDep
) -> list[ShortDiscussionResponse]:
    return await discussion_service.get_user_discussions(user_id)


@router.delete(
    "/discussions/{id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(rate_limit)]
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
    dependencies=[Depends(rate_limit)]
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
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(rate_limit)]
)
async def delete_message(
    id: UUID,
    user_id: UserIdDep,
    discussion_service: DiscussionServiceDep
) -> None:
    await discussion_service.delete_message(id, user_id)

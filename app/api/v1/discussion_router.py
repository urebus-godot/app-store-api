from uuid import UUID
import asyncio
import logging

from fastapi import APIRouter, status, Depends, WebSocket
from fastapi.websockets import WebSocketDisconnect

from pydantic import ValidationError

from app.core.config import settings
from app.core.exceptions import (
    InvalidTokenError, 
    InvalidTokenPayloadError
)
from app.schemas.discussion import (
    DiscussionRequest,
    DiscussionResponse,
    ShortDiscussionResponse,
    MessageRequest,
    MessageResponse
)
from app.schemas.ws_messages import incoming_adapter
from app.schemas.ws_events import (
    ErrorEvent
)
from app.api.deps import (
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

logger = logging.getLogger("api.v1.discussion_router")


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
) -> None:
    """WebSockets эндпоинт для обмена сообщения в обсуждении 
    в реальном времени. Первое сообщение должно содержать токен доступа
    для аутентификации пользователя.
    
    **Возвращает**: None"""
    await websocket.accept()
    try:
        logger.info("Awaiting data from websocket...")
        ws_data = await asyncio.wait_for(
            websocket.receive_json(), 
            timeout=settings.WS_AUTH_TIMEOUT
        )
        msg_type = ws_data.get("type", None)

        if msg_type is None or msg_type != "auth":
            await websocket.close(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="Wrong message type"
            )
            return
        
        user_id = validate_access_token(ws_data["token"], secret_key).user_id
        user = await user_repo.get_user_by_id(user_id)

        if not user:
            await websocket.close(
                code=status.WS_1003_UNSUPPORTED_DATA,
                reason="User not found"
            )

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
    except ValidationError as e:
        await websocket.send_json(
            ErrorEvent(detail=str(e)).model_dump(mode="json")
        )

    logger.info("Start getting discussion")
    discussion = await discussion_repo.get_discussion(id)
    
    if discussion is None:
        await websocket.close(
            code=status.WS_1003_UNSUPPORTED_DATA,
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
    dependencies=[Depends(rate_limit)],
    response_model=ShortDiscussionResponse
)
async def create_discussion(
    data: DiscussionRequest,
    app_id: UUID,
    user_id: UserIdDep,
    discussion_service: DiscussionServiceDep
) -> ShortDiscussionResponse:
    """Создаёт обсуждение в базе данных.
    
    **Возвращает**: ShortDiscussionResponse"""
    return await discussion_service.create_discussion(
        data, user_id, app_id
    )


@router.get(
    "/discussions/{id}",
    dependencies=[Depends(rate_limit)],
    response_model=DiscussionResponse
)
async def get_discussion(
    id: UUID, 
    skip_limit: SkipLimitParams,
    discussion_service: DiscussionServiceDep
) -> DiscussionResponse:
    """Находит обсуждение с указанным *id* в базе данных.
    
    **Возвращает**: DiscussionResponse"""
    skip, limit = skip_limit
    return await discussion_service.get_discussion(
        id=id, skip=skip, limit=limit
    )


@router.get(
    "/discussions/app/{app_id}",
    dependencies=[Depends(rate_limit)],
    response_model=list[ShortDiscussionResponse]
)
async def get_app_discussions(
    app_id: UUID, 
    skip_limit: SkipLimitParams,
    discussion_service: DiscussionServiceDep
) -> list[ShortDiscussionResponse]:
    """Находит обсуждения к приложению с указанным *id* в базе данных.
    
    **Возвращает**: list[ShortDiscussionResponse]"""
    skip, limit = skip_limit
    return await discussion_service.get_app_discussions(
        app_id=app_id, skip=skip, limit=limit
    )


@router.get(
    "/discussions/user/me",
    dependencies=[Depends(rate_limit)],
    response_model=list[ShortDiscussionResponse]
)
async def get_my_discussions(
    user_id: UserIdDep, 
    skip_limit: SkipLimitParams,
    discussion_service: DiscussionServiceDep
) -> list[ShortDiscussionResponse]:
    """Находит обсуждения, созданные текущим пользователем, в базе данных.
    
    **Возвращает**: list[ShortDiscussionResponse]"""
    skip, limit = skip_limit
    return await discussion_service.get_user_discussions(
        user_id=user_id, skip=skip, limit=limit
    )


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
    """Удаляет обсуждение с указанным *id* из базы данных.
    
    **Возвращает**: list[ShortDiscussionResponse]"""
    await discussion_service.delete_discussion(id, user_id)


# ------ Message routes ------ 

@router.post(
    "/discussions/{discussion_id}/messages",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit)],
    response_model=MessageResponse
)
async def create_message(
    data: MessageRequest,
    discussion_id: UUID,
    user_id: UserIdDep,
    discussion_service: DiscussionServiceDep
) -> MessageResponse:
    """Создаёт сообщение к обсуждению с указанным *discussion_id* 
    в базе данных.
    
    **Возвращает**: MessageResponse"""
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
    """Удаляет сообщение с указанным *id* из базы данных.
    
    **Возвращает**: None"""
    await discussion_service.delete_message(id, user_id)

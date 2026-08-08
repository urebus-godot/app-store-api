from uuid import UUID
from collections import defaultdict
from functools import wraps
import asyncio
import json

from fastapi import WebSocket
from redis.asyncio import Redis

from app.core.logging import logger


def log_function(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        logger.debug(f"Time to call {func.__name__}")
        result = await func
        logger.debug(f"Called {func.__name__}")
        return result
    return wrapper


class DiscussionWebsocketManager:
    def __init__(self, redis: Redis) -> None:
        self.redis = redis
        self.rooms: dict[UUID, set[WebSocket]] = defaultdict(set)
        self.listeners: dict[UUID, asyncio.Task] = {}

    @log_function
    async def connect(
        self, discussion_id: UUID, ws: WebSocket
    ) -> None:
        logger.debug(
            f"""
            Awaiting ws connect: 
            App state = {ws.application_state}, 
            Client state = {ws.client_state}, 
            User = {ws.user}
            """
            )
        await ws.accept()
        self.rooms[discussion_id].add(ws)
        if discussion_id not in self.listeners:
            self.listeners[discussion_id] = asyncio.create_task(
                self.listen(discussion_id)
            )
            logger.debug(
                f"Start listen for discussion with id {discussion_id}"
                )

    @log_function
    async def disconnect(
        self, discussion_id: UUID, ws: WebSocket
    ) -> None:
        room = self.rooms.get(discussion_id)

        if not room:
            logger.debug(f"Room with id {discussion_id} not found")
            return

        room.discard(ws)

        if not room:
            del self.rooms[discussion_id]
            logger.debug("Deleted room")
            task = self.listeners.pop(discussion_id, None)
            if task:
                task.cancel()
                logger.debug("Cancelled listen task")

    @log_function
    async def listen(
        self, discussion_id: UUID
    ) -> None:
        channel = f"discussions:{discussion_id}:messages"
        pubsub = await self.redis.pubsub()
        await pubsub.subscribe(channel)
        logger.debug(
            f"pubsub subscribed to channel of discussion {discussion_id}"
            )
        try:
            async for message in pubsub.listen():
                logger.debug(f"message that pubsub listen to: {message}")
                if message["type"] != "message":
                    continue
                data = json.loads(message["type"])
                await self.broadcast_local(discussion_id, data)
                logger.debug(
                    f"Broadcast. Data = {data}, Discussion = {discussion_id}"
                    )
        finally:
            await pubsub.unsubscribe(channel)

    @log_function
    async def broadcast_local(
        self, discussion_id: UUID, data: dict
    ) -> None:
        for ws in list(self.rooms.get(discussion_id, ())):
            try:
                await ws.send_json(data)
                logger.debug(f"Sent data = {data}")
            except Exception as e:
                logger.error(
                    f"Error occurred: {e}" 
                    f"Discard ws of discussion {discussion_id}"
                    )
                self.rooms[discussion_id].discard(ws)

    @log_function
    async def publish(
        self, discussion_id: UUID, data: dict
    ) -> None:
        channel = f"discussions:{discussion_id}:messages"
        await self.redis.publish(channel, json.dumps(data))
        logger.debug(
            f"Published data = {data} to the "
            f"{discussion_id} discussion channel"
            )

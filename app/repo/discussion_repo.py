from abc import ABC, abstractmethod
from uuid import UUID
from typing import Optional

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.models.discussion import (
    DiscussionDB, DiscussionRequest,
    MessageRequest, MessageDB
    )


class AbstractDiscussionRepository(ABC):
    @abstractmethod
    async def create_discussion(
        self, data: DiscussionRequest
    ) -> DiscussionDB:
        pass

    @abstractmethod
    async def get_discussion(
        self, id: UUID
    ) -> DiscussionDB:
        pass

    @abstractmethod
    async def delete_discussion(
        self, id: UUID
    ) -> DiscussionDB:
        pass

    @abstractmethod
    async def create_message(
        self, data: DiscussionRequest
    ) -> DiscussionDB:
        pass

    @abstractmethod
    async def get_message(self, id: UUID) -> Optional[DiscussionDB]:
        pass

    @abstractmethod
    async def delete_message(
        self, id: UUID
    ) -> DiscussionDB:
        pass

class DiscussionRepository(AbstractDiscussionRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_discussion(
        self, data: DiscussionRequest,
        user_id
    ) -> DiscussionDB:
        discussion = DiscussionDB(**data.model_dump())

        self.session.add(discussion)
        self.session.commit()

        return discussion

    async def get_discussion(
        self, id: UUID
    ) -> DiscussionDB:
        discussion = (await self.session.exec(
            select(DiscussionDB).where(DiscussionDB.id == id)
        )).one_or_none()
        return discussion

    async def delete_discussion(
        self, discussion: DiscussionDB
    ) -> DiscussionDB:
        await self.session.delete(discussion)
        self.session.commit()

        return {"message": "Discussion has been deleted"}

    async def create_message(
        self, data: MessageRequest, 
        author_id: UUID,
        discussion_id: UUID
    ) -> MessageDB:
        message = MessageDB(**data)
        message.author_id = author_id
        message.discussion_id = discussion_id

        self.session.add(message)
        self.session.commit()

        return message

    async def get_message(self, id: UUID) -> Optional[MessageDB]:
        message = (await self.session.exec(
            select(MessageDB).where(MessageDB.id == id)
        )).one_or_none()
        return message

    async def delete_message(
        self, message: MessageDB
    ) -> dict[str, str]:
        self.session.delete(message)
        self.session.commit()

        return {"message": "Message has been deleted"}
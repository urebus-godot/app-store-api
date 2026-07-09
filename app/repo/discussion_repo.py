from uuid import UUID
from typing import Optional

from sqlalchemy.orm import selectinload
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, desc

from app.models.discussion import (
    DiscussionDB, DiscussionRequest,
    MessageRequest, MessageDB
    )


class DiscussionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.load_discussion_attrs = (
            selectinload(DiscussionDB.messages, MessageDB.author),
            )
        self.load_message_attrs = (
            selectinload(MessageDB.author),
            selectinload(MessageDB.discussion)
            )

    async def create_discussion(
        self, data: DiscussionRequest,
        user_id: UUID, app_id: UUID
    ) -> DiscussionDB:
        discussion = DiscussionDB(**data.model_dump())
        discussion.creator_id = user_id
        discussion.app_id = app_id

        self.session.add(discussion)
        await self.session.commit()
        await self.session.refresh(discussion, attribute_names=["messages"])

        return discussion

    async def get_discussion(
        self, id: UUID
    ) -> DiscussionDB:
        discussion = (await self.session.exec(
            select(DiscussionDB).where(
                DiscussionDB.id == id
                ).options(selectinload(DiscussionDB.messages).selectinload(MessageDB.author))
        )).one_or_none()

        return discussion

    async def get_app_discussions(
        self, app_id: UUID
    ) -> list[DiscussionDB]:
        discussions = (await self.session.exec(
            select(DiscussionDB).where(
                DiscussionDB.app_id == app_id
                ).order_by(desc(DiscussionDB.created_at))
        )).all()

        return discussions

    async def get_user_discussions(
        self, user_id: UUID
    ) -> list[DiscussionDB]:
        discussions = (await self.session.exec(
            select(DiscussionDB).where(
                DiscussionDB.creator_id == user_id
                ).order_by(desc(DiscussionDB.created_at))
        )).all()

        return discussions

    async def delete_discussion(
        self, discussion: DiscussionDB
    ) -> None:
        await self.session.delete(discussion)
        await self.session.commit()

    async def create_message(
        self, data: MessageRequest, 
        author_id: UUID,
        discussion_id: UUID
    ) -> MessageDB:
        message = MessageDB(**data.model_dump())
        message.author_id = author_id
        message.discussion_id = discussion_id

        self.session.add(message)
        await self.session.commit()

        #id = message.id
        #message = (await self.session.exec(
        #    select(MessageDB).where(
        #        MessageDB.id == id
        #        ).options(*self.load_message_attrs)
        #    )).one()

        return message

    async def get_message(self, id: UUID) -> Optional[MessageDB]:
        message = (await self.session.exec(
            select(MessageDB).where(
                MessageDB.id == id
                ).options(*self.load_message_attrs)
        )).one_or_none()

        return message

    async def delete_message(
        self, message: MessageDB
    ) -> None:
        await self.session.delete(message)
        await self.session.commit()
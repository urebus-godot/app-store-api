from uuid import UUID

from app.core.exceptions import (
    message_not_found_exception,
    discussion_not_found_exception,
    no_rights_exception,
)
from app.core.logging import logger
from app.repo.discussion_repo import DiscussionRepository
from app.service.app_service import AppService

from app.models.discussion import (
    DiscussionDB,
    MessageDB
)
from app.schemas.discussion import (
    DiscussionRequest,
    MessageRequest
)

from app.uow.orm import UnitOfWork


class DiscussionService:
    def __init__(
        self, 
        discussion_repo: DiscussionRepository, 
        app_service: AppService,
        uow: UnitOfWork
    ):
        self.discussion_repo = discussion_repo
        self.app_service = app_service
        self.uow = uow

    async def create_discussion(
        self,
        data: DiscussionRequest,
        user_id: UUID,
        app_id: UUID
    ) -> DiscussionDB:
        async with self.uow:
            user = await self.uow.user_repo.get_user_by_id(user_id)
            app = await self.app_service.get_app(app_id)
            logger.info(app)
            discussion = await self.uow.discussion_repo.create_discussion(
                data, user, app_id
            )
            await self.uow.commit()
            
        return discussion

    async def get_discussion(self, id: UUID) -> DiscussionDB:
        discussion = await self.discussion_repo.get_discussion(id)
        if discussion is None:
            raise discussion_not_found_exception
        return discussion

    async def get_app_discussions(self, app_id: UUID) -> list[DiscussionDB]:
        discussions = await self.discussion_repo.get_app_discussions(app_id)
        return discussions

    async def get_user_discussions(self, user_id: UUID) -> list[DiscussionDB]:
        discussions = await self.discussion_repo.get_user_discussions(user_id)
        return discussions

    async def delete_discussion(
        self, id: UUID, user_id: UUID
    ) -> None:
        async with self.uow:
            discussion = await self.uow.discussion_repo.get_discussion(id)

            if discussion is None:
                raise discussion_not_found_exception
            if discussion.creator_id != user_id:
                raise no_rights_exception

            await self.uow.discussion_repo.delete_discussion(discussion)
            await self.uow.commit()

    async def create_message(
        self,
        data: MessageRequest,
        author_id: UUID,
        discussion_id: UUID
    ) -> MessageDB:
        async with self.uow:
            author = await self.uow.user_repo.get_user_by_id(author_id)
            await self.get_discussion(discussion_id)
            message = await self.uow.discussion_repo.create_message(
                data, author, discussion_id
            )
            await self.uow.commit()

        return message

    async def delete_message(
        self, id: UUID, user_id: UUID
    ) -> None:
        async with self.uow:
            message = await self.uow.discussion_repo.get_message(id)

            if message is None:
                raise message_not_found_exception

            if message.author_id != user_id:
                raise no_rights_exception

            await self.uow.session.delete(message)
            await self.uow.commit()
from uuid import UUID

from app.uow.unit_of_work import UnitOfWork
from app.core.exceptions import (
    message_not_found_exception,
    discussion_not_found_exception,
    no_rights_exception,
)
from app.core.logging import logger
from app.repo.discussion_repo import DiscussionRepository
from app.service.app_service import AppService
from app.models.discussion import (
    DiscussionRequest,
    DiscussionDB,
    MessageDB,
    MessageRequest,
)


class DiscussionService:
    def __init__(
        self, discussion_repo: DiscussionRepository, app_service: AppService
    ):
        self.discussion_repo = discussion_repo
        self.app_service = app_service

    async def create_discussion(
        self,
        data: DiscussionRequest,
        user_id: UUID,
        app_id: UUID,
        uow: UnitOfWork,
    ) -> DiscussionDB:
        async with uow:
            app = await self.app_service.get_app(app_id)
            logger.info(app)
            discussion = await self.discussion_repo.create_discussion(
                data, user_id, app_id
            )
            await uow.commit()

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
        self, id: UUID, user_id: UUID, uow: UnitOfWork
    ) -> None:
        async with uow:
            discussion = await self.discussion_repo.get_discussion(id)

            if discussion is None:
                raise discussion_not_found_exception
            if discussion.creator_id != user_id:
                raise no_rights_exception

            await self.discussion_repo.delete_discussion(discussion)
            await uow.commit()

    async def create_message(
        self,
        data: MessageRequest,
        author_id: UUID,
        discussion_id: UUID,
        uow: UnitOfWork,
    ) -> MessageDB:
        async with uow:
            await self.get_discussion(discussion_id)
            message = await self.discussion_repo.create_message(
                data, author_id, discussion_id
            )
            await uow.commit()
            message = await self.discussion_repo.get_message(message.id)
            return message

    async def delete_message(
        self, id: UUID, user_id: UUID, uow: UnitOfWork
    ) -> None:
        async with uow:
            message = await self.discussion_repo.get_message(id)

            if message is None:
                raise message_not_found_exception

            if message.author_id != user_id:
                raise no_rights_exception

            await self.discussion_repo.delete_message(message)
            await uow.commit()

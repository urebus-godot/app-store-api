from uuid import UUID

from app.core.exceptions import (
    message_not_found_exception, discussion_not_found_exception,
    no_rights_exception
    )
from app.repo.discussion_repo import DiscussionRepository
from app.models.discussion import (
    DiscussionRequest, DiscussionDB,
    MessageDB, MessageRequest
    )


class DiscussionService:
    def __init__(self, discussion_repo: DiscussionRepository):
        self.discussion_repo = discussion_repo

    async def create_discussion(
        self, data: DiscussionRequest, user_id: UUID
    ) -> DiscussionDB:
        discussion = await self.discussion_repo.create_discussion(
            data, user_id
            )
        return discussion

    async def get_discussion(
        self, id: UUID
    ) -> DiscussionDB:
        discussion = await self.discussion_repo.get_discussion(id)
        if discussion is None:
            raise discussion_not_found_exception
        return discussion

    async def delete_discussion(
        self, id: UUID
    ) -> DiscussionDB:
        discussion = await self.discussion_repo.get_discussion(id)
        if discussion is None:
            raise discussion_not_found_exception
        result = await self.discussion_repo.delete_discussion(discussion)
        return result

    async def create_message(
        self, data: DiscussionRequest, 
        author_id: UUID,
        discussion_id: UUID
    ) -> MessageDB:
        message = await self.discussion_repo.create_message(
            data, author_id=author_id, discussion_id=discussion_id
            )
        return message

    async def delete_message(
        self, id: UUID, user_id: UUID
    ) -> dict[str, str]:
        message = await self.discussion_repo.get_message(id)
        if message is None:
            raise message_not_found_exception
        if message.author_id != user_id:
            raise no_rights_exception
        result = await self.discussion_repo.delete_message(message)
        return result
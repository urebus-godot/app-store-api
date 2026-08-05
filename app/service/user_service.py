from typing import Optional, Union
from uuid import UUID
import asyncio
import os

from fastapi import BackgroundTasks, Request, UploadFile
from pydantic import EmailStr
from jwt.exceptions import DecodeError
import jwt

from app.db.redis import Redis

from app.base_models.user import UserRole
from app.models.user import UserDB
from app.schemas.user import UserRequest, UserUpdate
from app.schemas.token import LoginResponse
from app.models.file import UserProfilePicture

from app.repo.user_repo import UserRepository
from app.service.app_service import AppService

from app.task_queue.tasks.image_tasks import process_image
from app.utils.email_send import send_email

from app.core.exceptions import (
    user_not_found_exception,
    email_used_exception,
    username_used_exception,
    already_has_role_exception,
    incorrect_creds_exception,
    user_data_used_exception,
    invalid_refresh_token_exception,
    invalid_file_exception,
    file_too_large_exception,
    no_profile_pic_exception
)
from app.core.security import verify_password, get_password_hash
from app.core.auth import create_token_pair
from app.core.logging import logger
from app.core.config import settings
from app.utils.time import get_time_string

from app.uow.orm import UnitOfWork

from app.utils.files import write_file, to_megabytes


class UserService:
    def __init__(
        self, 
        user_repo: UserRepository,
        app_service: AppService,
        uow: UnitOfWork
    ):
        self.user_repo = user_repo
        self.app_service = app_service
        self.uow = uow

    async def username_registered(self, username: str) -> bool:
        return await self.user_repo.username_registered(username)

    async def email_registered(self, email: EmailStr) -> bool:
        return await self.user_repo.email_registered(email)

    async def register_user(
        self, data: UserRequest, 
    ) -> UserDB:
        async with self.uow:
            logger.info("Enter register_user func")
            username_used = await self.username_registered(data.username)
            logger.info(f"Username is being used: {username_used}")
            if username_used:
                raise username_used_exception

            if data.email is not None:
                email_used = await self.email_registered(data.email)
                logger.info(f"Email is being used: {email_used}")
                if email_used:
                    raise email_used_exception

            logger.info("Start registering user in the database")
            user = await self.uow.user_repo.register_user(data)
            logger.info("Registered user")

            await self.uow.commit()

        return user

    async def authenticate_user(
        self,
        username: str,
        password: str,
    ) -> Union[UserDB, False]:
        user = await self.get_user_by_username(username)
        logger.info(f"User found: {user.username}")

        if not user:
            verify_password(password, get_password_hash("dummypassword"))
            return False

        if not verify_password(password, user.hashed_password):
            return False

        return user

    async def login(
        self,
        username: str,
        password: str,
        bg_tasks: BackgroundTasks,
        request: Request,
        redis: Redis,
        sends_email: bool
    ) -> LoginResponse:
        user = await self.authenticate_user(username, password)

        if not user:
            raise incorrect_creds_exception

        email_body = settings.LOGIN_TEMPLATE % (
            request.client.host, get_time_string()
        )

        if user.email is not None and sends_email:
            bg_tasks.add_task(
                send_email,
                [str(user.email)],
                "Someone has logged into your account",
                email_body
            )

        tokens = await create_token_pair(str(user.id), redis)

        return LoginResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            user_id=user.id,
        )

    async def logout(
        self, refresh_token: str, redis: Redis, secret_key: str
    ) -> dict[str, str]:
        try:
            payload = jwt.decode(
                refresh_token,
                secret_key,
                algorithms=settings.JWT_ALGORITHM,
            )
            jti = payload.get("jti")
            ttl = await redis.ttl(f"refresh_token:{jti}")
            logger.info(f"{payload = }")
            logger.info(f"{ttl = }")
            if ttl > 0:
                await redis.set(f"blacklist:{jti}", "1", ex=ttl)
            await redis.delete(f"refresh_token:{jti}")

            return {"message": "Logout successful"}

        except DecodeError as e:
            logger.info(f"Exception = {e}")
            raise invalid_refresh_token_exception

    async def become_publisher(
        self, user: UserDB, 
    ) -> dict[str, str]:
        async with self.uow:
            if UserRole.PUBLISHER in user.roles:
                raise already_has_role_exception

            user = await self.uow.user_repo.get_user_by_id(user.id)
            result = await self.uow.user_repo.become_publisher(user)

            await self.uow.commit()

        return result

    async def upload_profile_picture(
        self, 
        request: Request,
        file: UploadFile, 
        user_id: UUID,
        
    ) -> UserProfilePicture:
        async with self.uow:
            extension = os.path.splitext(file.filename)[1]

            if extension not in settings.IMAGE_EXTENSIONS:
                raise invalid_file_exception

            file_size_mb = to_megabytes(file.size)
            if file_size_mb > settings.MAX_PROFILE_PICTURE_SIZE_MB:
                raise file_too_large_exception

            filename = f"{user_id}{extension}"
            file_path = settings.PROFILE_PICTURE_PATH / filename

            await asyncio.to_thread(
                write_file, 
                file, filename, settings.PROFILE_PICTURE_PATH
                )
            process_image.delay(
                str(file_path), (128, 128), 85
                )

            profile_picture = await self.uow.user_repo.get_profile_picture(user_id)

            if profile_picture is None:
                profile_picture = UserProfilePicture(
                    user_id=user_id,
                    extension=extension
                )
                self.uow.session.add(profile_picture)

            profile_picture.extension = extension

            await self.uow.commit()

        return profile_picture

    async def remove_profile_picture_by_user(
        self, 
        user_id: UUID, 
        
    ) -> None:
        async with self.uow:
            profile_picture = await self.uow.user_repo.get_profile_picture(
                user_id
                )

            if profile_picture is None:
                raise no_profile_pic_exception

            filename = f"{profile_picture.user_id}{profile_picture.extension}"
            profile_picture_path = (
                settings.PROFILE_PICTURE_PATH / filename
                )
            os.remove(profile_picture_path)
            await self.uow.session.delete(profile_picture)

            await self.uow.commit()

    async def remove_profile_picture(
        self, 
        user_id: UUID, 
        
    ) -> None:
        profile_picture = await self.uow.user_repo.get_profile_picture(
            user_id
            )

        if profile_picture is None:
            return

        filename = f"{profile_picture.user_id}{profile_picture.extension}"
        profile_picture_path = (
            settings.PROFILE_PICTURE_PATH / filename
            )
        os.remove(profile_picture_path)
        await self.uow.session.delete(profile_picture)

    async def update_user(
        self, user: UserDB, data: UserUpdate, 
    ):
        async with self.uow:
            if user.username == data.username or user.email == data.email:
                raise user_data_used_exception

            if await self.username_registered(data.username):
                raise username_used_exception

            if data.email is not None:
                if await self.email_registered(data.email):
                    raise email_used_exception
                
            data = data.model_dump(exclude_unset=True, exclude_none=True)
            user.sqlmodel_update(data)

            if "password" in data:
                user.hashed_password = get_password_hash(data["password"])

            await self.uow.commit()

        return user
    

    async def get_user_by_username(
        self, username: str
    ) -> Optional[UserDB]:
        user = await self.user_repo.get_user_by_username(username)

        if user is None:
            raise user_not_found_exception

        return user

    async def get_user_by_id(
        self, id: UUID
    ) -> Optional[UserDB]:
        user = await self.user_repo.get_user_by_id(id)

        if user is None:
            raise user_not_found_exception

        return user

    async def get_users(self, skip: int, limit: int) -> list[UserDB]:
        users = await self.user_repo.get_users(skip, limit)
        return users

    async def delete_user(
        self, 
        user_id: UUID, 
        redis: Redis, 
        
    ) -> None:
        async with self.uow:
            user = await self.uow.user_repo.get_user_by_id(user_id)

            if user is None:
                raise user_not_found_exception

            published_apps = await self.uow.app_repo.get_publisher_apps(
                user_id=user_id, public_only=False
                )

            for app in published_apps:
                await self.app_service.delete_app(app.id, self.uow)

            await redis.delete(f"user_tokens:{user_id}")
            await self.uow.session.delete(user)

            await self.uow.commit()
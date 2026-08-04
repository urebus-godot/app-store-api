from functools import lru_cache

from fastapi import Depends

from services.file_service import FileService
from storage.minio_repository import MinioStorage
from storage.protocols import ObjectStorage
from uow.protocols import UnitOfWork  # твоя существующая фабрика UoW


@lru_cache
def get_object_storage() -> ObjectStorage:
    # MinioStorage не держит постоянного соединения (клиент создаётся
    # внутри каждого метода через async with), поэтому его безопасно
    # переиспользовать как синглтон на всё приложение.
    return MinioStorage()


def get_file_service(
    storage: ObjectStorage = Depends(get_object_storage),
    uow: UnitOfWork = Depends(),  # подставь свой провайдер UoW
) -> FileService:
    return FileService(storage=storage, uow=uow)


def get_current_user_id():
    # заглушка — у тебя уже есть JWT-зависимость из refresh-token системы
    raise NotImplementedError

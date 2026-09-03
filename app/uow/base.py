from abc import ABC, abstractmethod
from typing import Self

from sqlmodel import SQLModel


class UnitOfWork(ABC):
    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        pass

    @abstractmethod
    async def commit(self) -> None:
        pass

    @abstractmethod
    async def rollback(self) -> None:
        pass

    @abstractmethod
    async def add(self, object: SQLModel) -> None:
        pass

    @abstractmethod
    async def delete(self, object: SQLModel) -> None:
        pass
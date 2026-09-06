from typing import Self, Protocol

from sqlmodel import SQLModel


class UnitOfWork(Protocol):
    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        pass

    async def commit(self) -> None:
        pass

    async def rollback(self) -> None:
        pass

    async def add(self, object: SQLModel) -> None:
        pass

    async def delete(self, object: SQLModel) -> None:
        pass
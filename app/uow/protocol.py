from typing import Self, Protocol

from sqlmodel import SQLModel


class UnitOfWork(Protocol):
    async def __aenter__(self) -> Self:
        ...

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        ...

    async def commit(self) -> None:
        ...

    async def rollback(self) -> None:
        ...

    def add(self, object: SQLModel) -> None:
        ...

    async def delete(self, object: SQLModel) -> None:
        ...
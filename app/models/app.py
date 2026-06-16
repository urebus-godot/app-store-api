from uuid import UUID, uuid4
from enum import StrEnum
from sqlmodel import SQLModel, Field

class GameGenre(StrEnum):
    ADVENTURE = "adventure"
    PUZZLE = "puzzle"
    RACING = "racing"
    SANDBOX = "sandbox"


class BaseApp(SQLModel):
    title: str
    description: str


class AppDB(BaseApp):
    id: UUID = Field(default_factory=lambda: uuid4())


class AppRequest(BaseApp):
    pass


class AppResponse(BaseApp):
    id: UUID


class AppUpdate(BaseApp):
    pass
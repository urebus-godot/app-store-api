from uuid import UUID, uuid4
from enum import StrEnum
from sqlmodel import SQLModel, Field


class BaseCompany(SQLModel):
    name: str
    founder_name: str
    address: str | None = Field()


class CompanyDB(BaseCompany):
    id: UUID = Field(default_factory=lambda: uuid4())


class CompanyRequest(BaseCompany):
    pass


class CompanyResponse(BaseCompany):
    id: UUID

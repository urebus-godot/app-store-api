from uuid import UUID, uuid4
from datetime import datetime, timezone

from sqlmodel import Field, Relationship
from sqlalchemy.dialects.postgresql import TIMESTAMP

from app.base_models.finance import BaseTransfer, OperationType


class TransferDB(BaseTransfer, table=True):
    __tablename__ = "transfers"

    id: UUID = Field(
        primary_key=True, default_factory=uuid4
        )
    user_id: UUID = Field(foreign_key="users.id", ondelete="CASCADE")
    user: "UserDB" = Relationship(
        back_populates="transfers"
    )
    made_at: datetime = Field(
        sa_type=TIMESTAMP(timezone=True),
        default_factory=lambda: datetime.now(timezone.utc)
        )
    operation_type: OperationType

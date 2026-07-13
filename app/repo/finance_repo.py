from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, desc

from app.models.finance import TransferRequest, TransferDB
from app.models.user import UserDB


class FinanceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.load_attrs = (
            
        )

    async def create_transfer(
        self, data: TransferRequest, user: UserDB
    ) -> dict[str, Decimal]:
        """Increase user's balance and create row in the db for transfer."""
        user.balance += data.amount

        transfer_db = TransferDB(amount=data.amount, user_id=user.id)

        self.session.add(transfer_db)
        await self.session.commit()

        return {"new_balance": user.balance}

    async def get_transfers(
        self, user_id: UUID
    ) -> list[TransferDB]:
        statement = (select(TransferDB)
        .where(TransferDB.user_id == user_id)
        .order_by(desc(TransferDB.made_at)))

        transfers = (await self.session.exec(
            statement
        )).all()

        return transfers
from uuid import UUID
from typing import Optional
from decimal import Decimal

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.models.app import AppRequest, AppDB, AppUpdate, GameGenre
from app.models.user import UserDB

async def upload_app(
    data: AppRequest, user_id: UUID, session: AsyncSession
) -> AppDB:
    app = AppDB(
        **data.model_dump(),
        publisher_id=user_id
    )
    session.add(app)
    await session.commit()
    await session.refresh(app)
    
    return app


async def add_app_to_purchases(
    user: UserDB, session: AsyncSession,
    id: Optional[UUID] = None,
    app: Optional[AppDB] = None
):
    if app is None:
        app = await get_app(id, session)

    user.apps_to_purchase.append(app)

    session.add(user)
    await session.commit()
    await session.refresh(user)

    return {"message": "App has been added to purchases"}


async def purchase_apps_in_purchases(
    user: UserDB, total_cost: Decimal, session: AsyncSession
):
    user.purchased_apps = user.purchased_apps + user.apps_to_purchase
    user.apps_to_purchase = []
    user.balance -= total_cost

    session.add(user)
    await session.commit()
    await session.refresh(user)

    return {"message": "Apps has been purchased"}


async def update_app(
    data: AppUpdate,
    session: AsyncSession,
    id: Optional[UUID] = None,
    app: Optional[AppDB] = None,
):
    if app is None:
        app = await get_app(id, session)

    data = data.model_dump(exclude_unset=True, exclude_none=True)

    app.sqlmodel_update(data)

    session.add(app)
    await session.commit()
    await session.refresh(app)

    return app


async def get_app(
    id: UUID,
    session: AsyncSession
):
    app = (await session.exec(
        select(AppDB).where(AppDB.id == id)
    )).one_or_none()
    return app


async def get_apps(
    session: AsyncSession, skip: int, limit: int
    ):
    apps = (await session.exec(
        select(AppDB).offset(skip).limit(limit)
    )).all()
    return apps


async def get_games(
    genre: GameGenre, session: AsyncSession,
    skip: int, limit: int
):
    games = (await session.exec(
        select(AppDB).where(
            AppDB.game_genre == genre
            ).offset(skip).limit(limit)
    )).all()
    return games


async def delete_app(
    session: AsyncSession,
    id: Optional[UUID] = None,
    app: Optional[AppDB] = None
):
    if app is None:
        app = await get_app(id, session)

    await session.delete(app)
    await session.commit()
    await session.flush(app)

    return {"detail": "App has been deleted"}
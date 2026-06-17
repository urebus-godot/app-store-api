from uuid import UUID

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.models.app import AppRequest, AppDB, AppUpdate


async def upload_app(
        request: AppRequest, session: AsyncSession
        ):
    app = AppDB(
        title=request.title,
        description=request.description
    )
    session.add(app)
    await session.commit()
    await session.refresh(app)
    
    return


async def update_app(
    data: AppUpdate,
    id: UUID,
    session: AsyncSession
    ):
    data = data.model_dump(exclude_unset=True)

    app = await get_app(id, session)
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


async def delete_app(
    id: UUID,
    session: AsyncSession
    ):
    app = await get_app(id, session)

    await session.delete(app)
    await session.commit()
    await session.flush(app)

    return {"detail": "App has been deleted"}
from uuid import UUID
from typing import Optional

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.repo.app_repo import get_app
from app.models.review import ReviewRequest, ReviewDB
from app.models.app import AppDB

async def create_review(
    data: ReviewRequest,
    user_id: UUID,
    session: AsyncSession,
    app_id: Optional[UUID] = None,
    app: Optional[AppDB] = None
) -> ReviewDB:
    if app is None:
        app = await get_app(app_id, session)

    review = ReviewDB(
        **data.model_dump(),
        author_id=user_id,
        #app_id=app.id,
        app=app
        )

    session.add(review)
    await session.commit()
    await session.refresh(review)

    return review


async def get_review(
    id: UUID,
    session: AsyncSession
) -> ReviewDB | None:
    review = (await session.exec(
        select(ReviewDB).where(ReviewDB.id == id)
    )).one_or_none()

    return review


async def get_app_reviews(
    session: AsyncSession,
    app_id: Optional[UUID] = None,
    app: Optional[AppDB] = None
) -> list[ReviewDB]:
    if app is None:
        app = await get_app(id=app_id, session=session)

    return app.reviews


async def delete_review(
    session: AsyncSession,    
    id: Optional[UUID] = None,
    review: Optional[ReviewDB] = None
) -> dict[str, str]:
    if review is None:
        review = await get_review(id, session)

    await session.delete(review)
    await session.commit()
    await session.flush(review)

    return {"message": "Review has been deleted"}
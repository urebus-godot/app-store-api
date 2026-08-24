from typing import Any

from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession
import pytest_asyncio
import pytest

from app.models.user import UserDB
from app.models.review import ReviewDB
from app.models.app import AppDB
from app.models.purchase import PurchaseDB


@pytest_asyncio.fixture
async def test_review(
    test_user: UserDB, test_app_2: AppDB, db_session: AsyncSession
):
    review = ReviewDB(
        rating=3,
        subject="It's OK",
        content="This app, well, it is quite alright for tests",
        author_id=test_user.id,
        app_id=test_app_2.id,
    )
    db_session.add(review)
    await db_session.flush()
    await db_session.refresh(review)

    return review


@pytest_asyncio.fixture
async def test_review_2(
    test_user_2: UserDB, test_app: AppDB, db_session: AsyncSession
):
    review = ReviewDB(
        rating=3,
        subject="It's OK",
        content="This app, well, it is quite alright for tests",
        author_id=test_user_2.id,
        app_id=test_app.id,
    )
    db_session.add(review)
    await db_session.commit()

    return review


class TestReviews:
    @pytest.mark.parametrize(
        argnames=["request_data", "expected_status_code", "create_purchase"],
        argvalues=[
            [
                {
                    "rating": 5,
                    "subject": "So Good!",
                    "content": "This app is so good for tests"
                },
                201,
                True
            ],
            [
                {
                    "rating": 1,
                    "subject": "So Good!",
                    "content": "This app is so good for tests"
                },
                201,
                True
            ],
            [
                {
                    "rating": 0,
                    "subject": "bad review",
                    "content": "this review is bad"
                },
                422,
                True
            ],
            [
                {
                    "rating": 100,
                    "subject": "bad review",
                    "content": "this review is bad"
                },
                422,
                True
            ],
            [
                {
                    "rating": 3,
                    "subject": "bad review",
                    "content": "this review is bad"
                },
                400,
                False
            ],
        ]
    )
    async def test_create_review(
        self, 
        auth_client: AsyncClient, 
        db_session: AsyncSession,
        test_user: UserDB,
        test_app_2: AppDB,
        request_data: dict[str, Any],
        expected_status_code: int,
        create_purchase: bool,
        logger
    ):
        if create_purchase:
            purchase = PurchaseDB(
                user_id=test_user.id,
                app_id=test_app_2.id,
                price=test_app_2.price
            )
            db_session.add(purchase)
            await db_session.flush()
            await db_session.refresh(purchase)

            response = await auth_client.post(
                f"/api/v1/carts/{test_user.id}/{test_app_2.id}"
            )
            response = await auth_client.post(
                "/api/v1/carts/checkout"
            )

        response = await auth_client.get(
            "/api/v1/apps/purchased/me"
        )
        logger.info(f"\n\n\nPurchased apps: {response.json()}\n\n")

        response = await auth_client.post(
            f"/api/v1/reviews/{test_app_2.id}",
            json=request_data,
        )
        logger.critical(f"\n\n\n{response.json()}\n\n\n")
        assert response.status_code == expected_status_code

    async def test_create_review_app_not_exists(
        self, auth_client: AsyncClient
    ):
        response = await auth_client.post(
            "/api/v1/reviews/097c51bc-3c31-4cdf-b726-a4b1df084d8e",
            json={
                "rating": 5,
                "subject": "So Good!",
                "content": "This app is so good for coding with bf!",
            },
        )
        assert response.status_code == 404

    async def test_create_review_own_app(
        self, auth_client: AsyncClient, test_app: AppDB
    ):
        response = await auth_client.post(
            f"/api/v1/reviews/{test_app.id}",
            json={
                "rating": 5,
                "subject": "My app is great",
                "content": "My app is so great!",
            },
        )
        assert response.status_code == 400

    async def test_get_app_reviews(
        self,
        auth_client: AsyncClient,
        test_review_2: ReviewDB,
        test_app: AppDB,
    ):
        response = await auth_client.get(f"/api/v1/reviews/{test_app.id}")
        data = response.json()

        assert response.status_code == 200
        assert len(data) == 1

    async def test_get_app_reviews_app_not_exists(
        self, auth_client: AsyncClient
    ):
        response = await auth_client.get(
            "/api/v1/reviews/097c51bc-3c31-4cdf-b726-a4b1df084d8e"
        )
        assert response.status_code == 404

    async def test_delete_review(
        self,
        auth_client: AsyncClient,
        test_user: UserDB,
        db_session: AsyncSession,
        test_app_2: AppDB,
    ):
        review = ReviewDB(
            rating=3,
            subject="test",
            content="app for tests",
            author_id=test_user.id,
            app_id=test_app_2.id,
        )
        db_session.add(review)
        await db_session.flush()
        await db_session.refresh(review)

        get_response = await auth_client.get(
            f"/api/v1/reviews/{test_app_2.id}"
        )
        print(f"\n\nReviews before delete{get_response.json()}\n\n")

        delete_response = await auth_client.delete(
            f"/api/v1/reviews/{review.id}"
        )
        assert delete_response.status_code == 204

        get_response = await auth_client.get(
            f"/api/v1/reviews/{test_app_2.id}"
        )
        print(f"\n\nReviews after delete{get_response.json()}\n\n")
        assert len(get_response.json()) == 0

    async def test_delete_review_no_rights(
        self, auth_client: AsyncClient, test_review_2: ReviewDB
    ):
        delete_response = await auth_client.delete(
            f"/api/v1/reviews/{test_review_2.id}"
        )
        assert delete_response.status_code == 403

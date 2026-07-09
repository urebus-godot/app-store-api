from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession
import pytest_asyncio

from app.models.user import UserDB
from app.models.review import ReviewDB
from app.models.app import AppDB


@pytest_asyncio.fixture
async def test_review(
    test_user: UserDB,
    test_app_2: AppDB,
    db_session: AsyncSession
    ):
    review = ReviewDB(
        rating=3,
        recap="It's OK",
        content="This app, well, it is quite alright for tests",
        author_id=test_user.id,
        app_id=test_app_2.id
    )
    db_session.add(review)
    await db_session.commit()

    return review

@pytest_asyncio.fixture
async def test_review_2(
    test_user_2: UserDB,
    test_app: AppDB,
    db_session: AsyncSession
    ):
    review = ReviewDB(
        rating=3,
        recap="It's OK",
        content="This app, well, it is quite alright for tests",
        author_id=test_user_2.id,
        app_id=test_app.id
    )
    db_session.add(review)
    await db_session.commit()

    return review


class TestReviews:
    async def test_create_review(
        self, auth_client: AsyncClient, test_app_2: AppDB
    ):
        response = await auth_client.post(
            f"/api/v1/reviews/{test_app_2.id}",
            json={
            "rating": 5,
            "recap": "So Good!", 
            "content": "This app is so good for coding with bf!"
                }
        )
        assert response.status_code == 201

    async def test_create_review_app_not_exists(
        self, auth_client: AsyncClient
    ):
        response = await auth_client.post(
            "/api/v1/reviews/097c51bc-3c31-4cdf-b726-a4b1df084d8e",
            json={
            "rating": 5,
            "recap": "So Good!", 
            "content": "This app is so good for coding with bf!"
                }
        )
        assert response.status_code == 404

    async def test_create_review_own_app(
        self, auth_client: AsyncClient, test_app: AppDB
    ):
        response = await auth_client.post(
            f"/api/v1/reviews/{test_app.id}",
            json={
            "rating": 5,
            "recap": "My app is great", 
            "content": "My app is so great!"
                }
        )
        assert response.status_code == 400

    async def test_get_app_reviews(
        self, 
        auth_client: AsyncClient, 
        test_review_2: ReviewDB, 
        test_app: AppDB
    ):
        response = await auth_client.get(
            f"/api/v1/reviews/{test_app.id}"
        )
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
        test_review: ReviewDB, 
        test_app_2: AppDB
    ):
        delete_response = await auth_client.delete(
            f"/api/v1/reviews/{test_review.id}"
        )
        assert delete_response.status_code == 204

        get_response = await auth_client.get(
            f"/api/v1/reviews/{test_app_2.id}"
        )
        assert len(get_response.json()) == 0

    async def test_delete_review_no_rights(
        self, 
        auth_client: AsyncClient, 
        test_review_2: ReviewDB
    ):
        delete_response = await auth_client.delete(
            f"/api/v1/reviews/{test_review_2.id}"
        )
        assert delete_response.status_code == 403

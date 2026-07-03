from typing import Annotated, Sequence, Optional
from string import punctuation

from fastapi import Query

from app.service.review_service import ReviewService
from app.models.app import AppDB, AppResponse, AppResponseWithPublisher
from app.models.review import ReviewDB
from app.core.config import settings
from app.core.logging import logger


def get_app_with_rating(
    app: AppDB, reviews: list[ReviewDB], 
    class_to_validate: str = "AppResponse"
) -> AppResponse:
    if reviews:
        match class_to_validate:
            case "AppResponse":
                app = AppResponse.model_validate(app)
            case "AppResponseWithPublisher":
                app = AppResponseWithPublisher.model_validate(app)
        rating = sum(
            [review.rating for review in reviews]
            ) / len(reviews)
        app.rating = round(rating, 1)
    return app


async def get_apps_with_rating(
    apps: list[AppDB],
    review_service: ReviewService
) -> list[AppResponse]:
    for app in apps:
        reviews = await review_service.get_app_reviews(app.id)
        app = get_app_with_rating(app, reviews)
    return apps


SearchQuery = Annotated[
    str, Query(
        default=None, description="Enter keywords separated by 1 space"
        )
]

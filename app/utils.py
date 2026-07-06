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
    class_to_validate: type = AppResponseWithPublisher
) -> AppResponse:
    logger.info(f"{reviews = }\n")
    if reviews:
        app = class_to_validate.model_validate(app)
        rating = sum(
            [review.rating for review in reviews]
            ) / len(reviews)
        app.rating = round(rating, 1)
    return app


async def get_apps_with_rating(
    apps: list[AppDB],
    review_service: ReviewService,
    class_to_validate: type = AppResponseWithPublisher
) -> list[AppResponse]:
    new_apps = []
    for app in apps:
        reviews = await review_service.get_app_reviews(app.id)
        app_response = get_app_with_rating(app, reviews, class_to_validate)
        new_apps.append(app_response)
        logger.info(type(app_response))
    return new_apps


SearchQuery = Annotated[
    str, Query(
        default=None, description="Enter keywords separated by 1 space"
        )
]

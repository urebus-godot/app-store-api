from .user import (
    UserDB,
    UserResponse,
    CurrentUserResponse,
    PublisherResponse,
    UserBaseResponse,
)
from .review import ReviewDB, ReviewResponse
from .app import (
    AppDB,
    AppResponse,
    GameResponse,
    AppResponseWithReviews,
    AppResponseWithPublisher,
    GameResponseWithPublisher,
)
from .purchase import (
    PurchaseDB,
    CartItem,
    CartResponse,
    CartItemResponse,
    PurchaseResponse,
)
from .discussion import (
    MessageResponse,
    ShortDiscussionResponse,
    DiscussionResponse,
)

UserDB.model_rebuild()
ReviewDB.model_rebuild()
AppDB.model_rebuild()
PurchaseDB.model_rebuild()
CartItem.model_rebuild()

UserResponse.model_rebuild()
CurrentUserResponse.model_rebuild()
PublisherResponse.model_rebuild()
UserBaseResponse.model_rebuild()

ReviewResponse.model_rebuild()

AppResponse.model_rebuild()
AppResponseWithReviews.model_rebuild()
AppResponseWithPublisher.model_rebuild()
GameResponse.model_rebuild()
GameResponseWithPublisher.model_rebuild()

PurchaseResponse.model_rebuild()
CartResponse.model_rebuild()
CartItemResponse.model_rebuild()

MessageResponse.model_rebuild()
ShortDiscussionResponse.model_rebuild()
DiscussionResponse.model_rebuild()

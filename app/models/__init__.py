from app.schemas.user import (
    UserResponse,
    CurrentUserResponse,
    PublisherResponse,
    UserBaseResponse
)
from app.schemas.review import ReviewResponse
from app.schemas.app import (
    AppResponse,
    GameResponse,
    AppResponseWithReviews,
    AppResponseWithPublisher,
    GameResponseWithPublisher
)

from app.schemas.purchase import (
    CartResponse,
    CartItemResponse,
    PurchaseResponse
)
from app.schemas.discussion import (
    MessageResponse,
    ShortDiscussionResponse,
    DiscussionResponse,
)
#from app.models.discussion import DiscussionDB, MessageDB
#from app.models.review import ReviewDB
#from app.models.finance import TransferDB
#from app.models.purchase import CartDB, CartItem, PurchaseDB
#from app.models.user import UserDB

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

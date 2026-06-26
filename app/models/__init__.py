from .user import UserDB, UserResponse
from .review import ReviewDB, ReviewResponse
from .app import AppDB, AppResponse
from .app_purchase import Purchase, CartItem

UserDB.model_rebuild()
ReviewDB.model_rebuild()
AppDB.model_rebuild()
Purchase.model_rebuild()
CartItem.model_rebuild()

UserResponse.model_rebuild()
ReviewResponse.model_rebuild()
AppResponse.model_rebuild()
#AppPurchaseResponse.model_rebuild()
#CartAppResponse.model_rebuild()
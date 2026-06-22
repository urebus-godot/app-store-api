from .user import UserDB
from .review import ReviewDB
from .app import AppDB

UserDB.model_rebuild()
ReviewDB.model_rebuild()
AppDB.model_rebuild()
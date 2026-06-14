from sqlmodel import SQLModel, Field

class BaseApp(SQLModel):
    title: str


class AppDB(BaseApp):
    pass


class AppRequest(BaseApp):
    pass


class AppResponse(BaseApp):
    pass
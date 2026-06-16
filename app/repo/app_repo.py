from sqlmodel.ext.asyncio.session import AsyncSession

async def app_exists(
        session: AsyncSession,
        app_id: str
        ) -> bool:
    return


async def upload_app(
        request: AppRequest, session: AsyncSession
        ):
    return


async def update_app(
    update: AppUpdate,
    session: AsyncSession
    ):
    return


async def get_app(
    id: str,
    session: AsyncSession
    ):
    return


async def get_apps(
    tags: set[str],
    session: AsyncSession
    ):
    return


async def delete_app(
    user: UserDB,
    session: AsyncSession
    ):
    return
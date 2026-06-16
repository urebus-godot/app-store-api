from fastapi import APIRouter
from app.core.dependencies import SessionDep, UserDep
from app.models.user import UserRequest
from app.service import user_service

router = APIRouter(prefix="/api/v1")


@router.post("/users/register-user")
async def register_user(
    request: UserRequest,
    session: SessionDep
    ):
    return await user_service.register_user(request, session)


@router.post("/users/register-user")
async def send_bid_to_become_developer(
    request: UserRequest,
    session: SessionDep
    ):    
    return await user_service.send_bid_to_become_developer(
        request, session)


@router.get("/users/{username}")
async def get_user(
    username: str,
    session: SessionDep
    ):
    return await user_service.get_user(username, session)


@router.get("/users/{username}")
async def update_current_user(
    username: str,
    session: SessionDep
    ):
    return await user_service.update_current_user(username, session)


@router.delete("/users/{username}")
async def delete_current_user(
    user: UserDep,
    session: SessionDep
    ):
    return await user_service.delete_user(user, session)
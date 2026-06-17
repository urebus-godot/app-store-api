from decimal import Decimal

from fastapi import APIRouter

from app.core.dependencies import SessionDep, UserDep
from app.models.user import UserRequest
from app.service import company_service

router = APIRouter(prefix="/api/v1")


@router.post("/users/register-user")
async def register_company(
    request: UserRequest,
    session: SessionDep
    ):
    return await company_service.register_company(request, session)


@router.get("/users/{username}")
async def update_current_user(
    username: str,
    session: SessionDep
    ):
    return await company_service.update_user(username, session)


@router.post("/users/me/increase-balance")
async def increase_balance(
    amount: Decimal,
    user: UserDep,
    session: SessionDep
    ):
    return await company_service.increase_balance(amount, session, username=user.username)


@router.get("/users/{username}")
async def get_user(
    username: str,
    session: SessionDep
    ):
    return await company_service.get_user(session, username=username)


@router.get("/users")
async def get_users(
    search_query: str,
    session: SessionDep
    ):
    return await company_service.get_users(search_query, session)


@router.delete("/users/{username}")
async def delete_current_user(
    user: UserDep,
    session: SessionDep
    ):
    return await company_service.delete_user(user, session)
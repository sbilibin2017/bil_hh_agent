from typing import Any, Callable, Coroutine

from fastapi import APIRouter

from backend.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
)
from backend.services.auth import AuthService


def create_auth_router(
    svc: AuthService,
    transaction: Callable[
        [Callable[..., Coroutine[Any, Any, Any]]],
        Callable[..., Coroutine[Any, Any, Any]],
    ],
) -> APIRouter:
    router = APIRouter(prefix="/auth", tags=["auth"])

    @router.post("/register")
    @transaction
    async def register(req: RegisterRequest) -> RegisterResponse:
        return await svc.register(req)

    @router.post("/login")
    async def login(req: LoginRequest) -> LoginResponse:
        return await svc.login(req)

    return router

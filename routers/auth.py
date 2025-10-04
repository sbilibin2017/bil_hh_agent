import logging
from typing import Any, Callable, Coroutine

from fastapi import APIRouter

from schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
)
from services.auth import AuthService

logger = logging.getLogger(__name__)


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
        logger.info(f"API call: /auth/register for username: {req.username}")
        try:
            response = await svc.register(req)
            logger.info(f"User registered successfully: {req.username}")
            return response
        except Exception as e:
            logger.error(f"Registration failed for {req.username}: {e}")
            raise

    @router.post("/login")
    async def login(req: LoginRequest) -> LoginResponse:
        logger.info(f"API call: /auth/login for username: {req.username}")
        try:
            response = await svc.login(req)
            logger.info(f"User logged in successfully: {req.username}")
            return response
        except Exception as e:
            logger.warning(f"Login failed for {req.username}: {e}")
            raise

    return router

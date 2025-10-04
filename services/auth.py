import logging
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import HTTPException, status

from repositories.user import UserRepository
from schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
)

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(
        self,
        user_repo: UserRepository,
        jwt_secret: str,
        jwt_algorithm: str = "HS256",
        jwt_expires_minutes: int = 1440,
    ) -> None:
        self.user_repo = user_repo
        self.jwt_secret = jwt_secret
        self.jwt_algorithm = jwt_algorithm
        self.jwt_expires_minutes = jwt_expires_minutes
        logger.info("AuthService initialized.")

    async def register(self, data: RegisterRequest) -> RegisterResponse:
        logger.info(f"Attempting to register user: {data.username}")
        existing_user = await self.user_repo.get_by_username(data.username)
        if existing_user:
            logger.warning(f"Registration failed: username '{data.username}' already exists")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Имя пользователя уже существует",
            )

        password_hash: str = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()
        user = await self.user_repo.save(
            username=data.username,
            email=str(data.email),
            password_hash=password_hash,
        )

        if not user:
            logger.error(f"Failed to save user '{data.username}' in repository")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Внутренняя ошибка сервиса",
            )

        logger.info(f"User registered successfully: {data.username}")
        return RegisterResponse(**user)

    async def login(self, data: LoginRequest) -> LoginResponse:
        logger.info(f"Attempting login for user: {data.username}")
        user = await self.user_repo.get_by_username(data.username)
        if not user:
            logger.warning(f"Login failed: user '{data.username}' not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден",
            )

        if not bcrypt.checkpw(data.password.encode(), user["password_hash"].encode()):
            logger.warning(f"Login failed: invalid password for user '{data.username}'")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный пароль",
            )

        payload = {
            "user_uuid": str(user["user_uuid"]),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=self.jwt_expires_minutes),
        }
        token: str = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        logger.info(f"User logged in successfully: {data.username}")
        return LoginResponse(token=token)


auth_service: AuthService | None = None

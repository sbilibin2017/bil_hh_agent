from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from backend.repositories.user import UserRepository


class AuthError(Exception):
    """Базовое исключение для ошибок аутентификации и регистрации."""


class UserAlreadyExistsError(AuthError):
    pass


class UserNotFoundError(AuthError):
    pass


class InvalidPasswordError(AuthError):
    pass


class AuthService:
    """
    Сервис для аутентификации и регистрации пользователей.

    :param user_repo: Репозиторий пользователей
    :param jwt_secret: Секретный ключ для генерации JWT
    :param jwt_algorithm: Алгоритм шифрования JWT (по умолчанию 'HS256')
    :param jwt_expires_minutes: Время жизни JWT в минутах (по умолчанию 1440)
    """

    def __init__(
        self,
        user_repo: UserRepository,
        jwt_secret: str,
        jwt_algorithm: str = "HS256",
        jwt_expires_minutes: int = 1440,
    ):
        self.user_repo = user_repo
        self.jwt_secret = jwt_secret
        self.jwt_algorithm = jwt_algorithm
        self.jwt_expires_minutes = jwt_expires_minutes

    async def register(self, username: str, email: str, password: str) -> None:
        """
        Регистрирует нового пользователя. Пароль хешируется перед сохранением.

        :param username: Имя пользователя
        :param email: Email пользователя
        :param password: Пароль в открытом виде
        :raises UserAlreadyExistsError: Если имя пользователя уже существует
        :raises AuthError: Если пользователь не может быть создан
        """
        existing_user = await self.user_repo.get_by_username(username)
        if existing_user:
            raise UserAlreadyExistsError()

        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        user = await self.user_repo.save(
            username=username,
            password_hash=password_hash,
            email=email,
        )
        if not user:
            raise AuthError()

    async def login(self, username: str, password: str) -> str:
        """
        Аутентификация пользователя. Возвращает JWT при успешном входе.

        :param username: Имя пользователя
        :param password: Пароль в открытом виде
        :return: JWT токен
        :raises UserNotFoundError: Если пользователь не найден
        :raises InvalidPasswordError: Если пароль неверный
        """
        user = await self.user_repo.get_by_username(username)
        if not user:
            raise UserNotFoundError()

        if not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
            raise InvalidPasswordError()

        payload = {
            "user_uuid": user["user_uuid"],
            "exp": datetime.now(timezone.utc) + timedelta(minutes=self.jwt_expires_minutes),
        }
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        return token

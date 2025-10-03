from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.db import DBContext
from backend.repositories.models.user import UserDB


class UserRepository:
    """
    Репозиторий для работы с пользователями.
    """

    def __init__(self, db_context: DBContext):
        self.db_context = db_context

    async def save(
        self,
        username: str,
        password_hash: str,
        email: str,
    ) -> dict | None:
        """
        Создает нового пользователя или обновляет существующего (по email).

        :return: dict с данными пользователя или None при ошибке
        """
        try:
            session: AsyncSession = await self.db_context.get_session()
            now = datetime.now(timezone.utc)
            stmt = (
                insert(UserDB)
                .values(
                    username=username,
                    password_hash=password_hash,
                    email=email,
                    created_at=now,
                    updated_at=now,
                )
                .on_conflict_do_update(
                    index_elements=[UserDB.email],
                    set_={
                        "username": username,
                        "password_hash": password_hash,
                        "updated_at": now,
                    },
                )
                .returning(UserDB)
            )

            result = await session.execute(stmt)
            user = result.scalar_one()
            return {
                "user_uuid": str(user.user_uuid),
                "username": user.username,
                "email": user.email,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
            }
        except SQLAlchemyError:
            return None

    async def get_by_username(self, username: str) -> dict | None:
        """
        Получает пользователя по имени.

        :return: dict с данными пользователя или None если не найден
        """
        try:
            session: AsyncSession = await self.db_context.get_session()
            stmt = select(UserDB).where(UserDB.username == username)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            if user is None:
                return None
            return {
                "user_uuid": str(user.user_uuid),
                "username": user.username,
                "email": user.email,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
            }
        except SQLAlchemyError:
            return None

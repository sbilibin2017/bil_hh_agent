import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError

from engines.db import DBContext
from repositories.models.user import UserDB

logger = logging.getLogger(__name__)


class UserRepository:
    """
    Репозиторий для работы с пользователями.
    Использует DBContext для получения текущей сессии.
    """

    def __init__(self, db_context: DBContext) -> None:
        self.db_context = db_context
        logger.info("UserRepository initialized.")

    async def save(self, username: str, password_hash: str, email: str) -> dict | None:  # type: ignore
        session = await self.db_context.get_session()
        now = datetime.now(timezone.utc)

        try:
            logger.info(f"Saving user: username={username}, email={email}")
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
            logger.info(f"User saved: user_uuid={user.user_uuid}")
            return {
                "user_uuid": str(user.user_uuid),
                "username": user.username,
                "email": user.email,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
            }
        except SQLAlchemyError as e:
            logger.error(f"Error saving user {username}: {e}")
            return None

    async def get_by_username(self, username: str) -> dict | None:  # type: ignore
        session = await self.db_context.get_session()

        try:
            logger.info(f"Fetching user by username: {username}")
            stmt = select(UserDB).where(UserDB.username == username)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            if user is None:
                logger.info(f"User not found: {username}")
                return None
            logger.info(f"User found: user_uuid={user.user_uuid}")
            return {
                "user_uuid": str(user.user_uuid),
                "username": user.username,
                "email": user.email,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
            }
        except SQLAlchemyError as e:
            logger.error(f"Error fetching user {username}: {e}")
            return None


user_repository: UserRepository | None = None

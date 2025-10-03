from contextvars import ContextVar
from functools import wraps
from typing import Any, Callable, Concatenate, Coroutine, TypeVar

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from typing_extensions import ParamSpec

engine: AsyncEngine | None = None
session_factory: async_sessionmaker[AsyncSession] | None = None

P = ParamSpec("P")
R = TypeVar("R")


class DBContext:
    """
    Контекст базы данных с хранением текущей сессии в ContextVar.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory
        self._current_session: ContextVar[AsyncSession | None] = ContextVar("current_session", default=None)

    def get_current_session(self) -> AsyncSession | None:
        """Возвращает текущую сессию (если она установлена)."""
        return self._current_session.get()

    def set_current_session(self, session: AsyncSession | None) -> None:
        """Устанавливает текущую сессию в контекст."""
        self._current_session.set(session)

    async def get_session(self) -> AsyncSession:
        """
        Возвращает текущую сессию из контекста,
        либо создаёт новую, если её нет.
        """
        session = self.get_current_session()
        if session is None:
            session = self._session_factory()
            self.set_current_session(session)
        return session

    def transaction(
        self, func: Callable[Concatenate[AsyncSession, P], Coroutine[Any, Any, R]]
    ) -> Callable[P, Coroutine[Any, Any, R]]:
        """
        Декоратор для асинхронных функций (хендлеров/сервисов),
        запускающий выполнение в транзакции.
        Если уже есть сессия — используется она.
        Иначе создаётся новая.
        """

        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            session = self.get_current_session()

            if session is None:
                session = await self.get_session()
                self.set_current_session(session)

                try:
                    result = await func(session, *args, **kwargs)
                    return result
                finally:
                    self.set_current_session(None)
                    await session.close()
            else:
                return await func(session, *args, **kwargs)

        return wrapper


db_context: DBContext | None = None

from contextvars import ContextVar

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class DBContext:
    """
    Транзакционный контекст для управления AsyncSession на каждый запрос/контекст.
    Использует переданную фабрику сессий (async_sessionmaker) и хранит текущую
    сессию в contextvars, чтобы повторно использовать одну сессию внутри запроса.
    """

    def __init__(self, async_session_factory: async_sessionmaker[AsyncSession]):
        """
        Инициализация контекста с указанной фабрикой асинхронных сессий.

        :param async_session_factory: async_sessionmaker для создания сессий
        """
        self._session_factory: async_sessionmaker[AsyncSession] = async_session_factory
        self._session_ctx: ContextVar[AsyncSession | None] = ContextVar("_session_ctx", default=None)

    async def get_session(self) -> AsyncSession:
        """
        Получает существующую сессию из contextvars или создает новую через фабрику.
        Сессия сохраняется в contextvars для повторного использования в рамках запроса.

        :return: Асинхронная сессия SQLAlchemy
        """
        session = self._session_ctx.get()
        if session is None:
            session = self._session_factory()
            self._session_ctx.set(session)
        return session

    def reset(self) -> None:
        """
        Сбрасывает текущую сессию в contextvars.
        Используется после завершения запроса или транзакции,
        чтобы избежать повторного использования старой сессии.
        """
        self._session_ctx.set(None)

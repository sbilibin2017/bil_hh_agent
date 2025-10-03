import contextvars
import logging
from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.sql import Executable, Select


class PostgresEngine:
    """
    Класс-обёртка для управления асинхронным SQLAlchemy движком и сессиями.
    Lazy initialization: движок и фабрика сессий создаются только при connect().
    """

    _session_var: contextvars.ContextVar[AsyncSession | None] = contextvars.ContextVar(
        "current_async_session", default=None
    )

    def __init__(
        self,
        database_url: str,
        pool_size: int = 10,
        max_overflow: int = 20,
        echo: bool = False,
    ):
        self._database_url = database_url
        self._pool_size = pool_size
        self._max_overflow = max_overflow
        self._echo = echo

        self.engine: AsyncEngine | None = None
        self.session_factory: async_sessionmaker[AsyncSession] | None = None

    async def connect(self) -> None:
        """Инициализация AsyncEngine и sessionmaker"""
        if self.engine is None:
            self.engine = create_async_engine(
                self._database_url,
                pool_pre_ping=True,
                pool_size=self._pool_size,
                max_overflow=self._max_overflow,
                echo=self._echo,
                future=True,
            )
            self.session_factory = async_sessionmaker(
                bind=self.engine,
                autoflush=False,
                autocommit=False,
                expire_on_commit=False,
                class_=AsyncSession,
            )

        logging.info("Успешное соединение с БД")

    async def dispose(self) -> None:
        """Закрыть соединения движка"""
        if self.engine:
            logging.info("Закрываем соединения с БД...")
            await self.engine.dispose()
            self.engine = None
            self.session_factory = None



    async def execute(self, stmt: Executable, to_commit: bool = True) -> None:
        """
        Выполнить INSERT/UPDATE/DELETE
        :param stmt: SQLAlchemy statement
        :param to_commit: если True, выполняется commit, иначе только flush
        """
        async for session in self._get_session():
            await session.execute(stmt)
            if to_commit:
                await session.commit()
            else:
                await session.flush()

    async def select(self, stmt: Select) -> list[dict[str, Any]]:
        """Выполнить SELECT и вернуть список строк в виде словарей"""
        async for session in self._get_session():
            result = await session.execute(stmt)
            rows = [dict(row) for row in result.mappings().all()]
            return rows
        return []

    async def select_one(self, stmt: Select) -> dict[str, Any] | None:
        """Выполнить SELECT и вернуть одну строку (или None)"""
        async for session in self._get_session():
            result = await session.execute(stmt)
            row = result.mappings().first()
            return dict(row) if row else None
        return None

    async def _get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Dependency для FastAPI (только внутри класса)"""
        if self.session_factory is None:
            raise RuntimeError("PostgresEngine не подключён. Вызовите connect() перед использованием get_session().")

        existing_session = self._session_var.get()
        if existing_session:
            yield existing_session
            return

        async with self.session_factory() as session:
            token = self._session_var.set(session)
            try:
                yield session
            finally:
                self._session_var.reset(token)

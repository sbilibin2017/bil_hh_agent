import argparse
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

import uvicorn
from fastapi import APIRouter, FastAPI
from pydantic import BaseSettings, Field
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.db.db import DBContext
from backend.repositories.user import UserRepository
from backend.routers.auth import create_auth_router
from backend.services.auth import AuthService


class Config(BaseSettings):
    """
    Конфигурация приложения и базы данных.
    """

    APP_NAME: str = Field(default="FastAPI App", description="Название приложения")
    APP_DESCRIPTION: str = Field(default="ИИ-агент для поиска вакансий на hh.ru", description="Описание приложения")
    DEBUG: bool = Field(default=False, description="Флаг отладки")
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Уровень логирования"
    )
    HOST: str = Field(default="127.0.0.1", description="Хост для запуска сервера")
    PORT: int = Field(default=8000, description="Порт для запуска сервера")
    API_VERSION: str = Field(default="/api/v1", description="Версия API с префиксом")
    WORKERS: int = Field(default=1, ge=1, description="Количество воркеров Uvicorn")
    POSTGRES_HOST: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_DB: str = Field(default="ai_job_agent")
    POSTGRES_USER: str = Field(default="ai_job_agent_user")
    POSTGRES_PASSWORD: str = Field(default="ai_job_agent_password")
    POSTGRES_POOL_SIZE: int = Field(default=10, ge=1)
    POSTGRES_IDLE_CONNECTIONS: int = Field(default=2, ge=0)
    HH_API_KEY: str
    CHATGPT_API_KEY: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = Field(default="HS256", description="Алгоритм JWT")
    JWT_EXPIRES_MINUTES: int = Field(default=1440, description="Время жизни JWT в минутах")

    @property
    def DATABASE_DSN(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


class App:
    """
    Класс-обертка для FastAPI приложения с методами, возвращающими None.
    """

    def __init__(self):
        self.config: Config | None = None
        self.app: FastAPI | None = None
        self.env_file: str = ".env"

    def parse_args(self) -> None:
        """
        Разбор аргументов командной строки для указания .env файла.
        """
        parser = argparse.ArgumentParser(description="FastAPI App с конфигом")
        parser.add_argument("--env-file", type=str, default=".env")
        args = parser.parse_args()
        self.env_file = args.env_file

    def parse_config(self) -> None:
        """
        Создание объекта конфигурации из .env файла.
        """
        if not Path(self.env_file).exists():
            raise FileNotFoundError(f"Файл '{self.env_file}' не найден")
        self.config = Config(_env_file=self.env_file)

    def configure_logging(self) -> None:
        """
        Настройка логирования согласно конфигурации.
        """
        if self.config is None:
            raise RuntimeError("Конфигурация не загружена. Вызовите parse_config() сначала.")

        numeric_level = getattr(logging, self.config.LOG_LEVEL.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError(f"Неверный уровень логирования: {self.config.LOG_LEVEL}")
        logging.basicConfig(
            level=numeric_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    def create_app(self) -> None:
        """
        Создание экземпляра FastAPI с базой данных, сервисами и роутерами.
        """
        if self.config is None:
            raise RuntimeError("Конфигурация не загружена. Вызовите parse_config() сначала.")

        async_engine = create_async_engine(
            self.config.DATABASE_DSN,
            echo=True,
            pool_size=self.config.POSTGRES_POOL_SIZE,
            max_overflow=self.config.POSTGRES_IDLE_CONNECTIONS,
            pool_pre_ping=True,
        )

        async_session_factory = async_sessionmaker(
            bind=async_engine,
            expire_on_commit=False,
            class_=AsyncSession,
        )

        db_context = DBContext(async_session_factory=async_session_factory)
        user_repository = UserRepository(db_context=db_context)
        auth_service = AuthService(
            user_repo=user_repository,
            jwt_secret=self.config.JWT_SECRET,
            jwt_algorithm=self.config.JWT_ALGORITHM,
            jwt_expires_minutes=self.config.JWT_EXPIRES_MINUTES,
        )

        auth_router = create_auth_router(auth_service)

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            yield
            await async_engine.dispose()

        self.app = FastAPI(
            title=self.config.APP_NAME,
            description=self.config.APP_DESCRIPTION,
            debug=self.config.DEBUG,
            lifespan=lifespan,
        )

        router = APIRouter(prefix=self.config.API_VERSION)
        router.include_router(auth_router)
        self.app.include_router(router)

    def run_uvicorn(self) -> None:
        """
        Запуск приложения через Uvicorn.
        """
        if self.app is None or self.config is None:
            raise RuntimeError("Приложение не готово. Вызовите parse_config() и create_app() сначала.")

        uvicorn.run(
            self.app,
            host=self.config.HOST,
            port=self.config.PORT,
            log_level=self.config.LOG_LEVEL.lower(),
            reload=self.config.DEBUG and self.config.WORKERS == 1,
            workers=self.config.WORKERS,
        )

import argparse
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

import uvicorn
from fastapi import APIRouter, FastAPI
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.engines import db
from backend.repositories import user as user_repo
from backend.routers.auth import create_auth_router
from backend.services import auth as auth_svc


class Config(BaseSettings):
    APP_NAME: str = Field(default="FastAPI App")
    APP_DESCRIPTION: str = Field(default="ИИ-агент для поиска вакансий на hh.ru")
    DEBUG: bool = Field(default=False)
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(default="INFO")
    HOST: str = Field(default="127.0.0.1")
    PORT: int = Field(default=8000)
    API_VERSION: str = Field(default="/api/v1")
    WORKERS: int = Field(default=1, ge=1)
    POSTGRES_HOST: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_DB: str = Field(default="ai_job_agent")
    POSTGRES_USER: str = Field(default="ai_job_agent_user")
    POSTGRES_PASSWORD: str = Field(default="ai_job_agent_password")
    POSTGRES_POOL_SIZE: int = Field(default=10, ge=1)
    POSTGRES_IDLE_CONNECTIONS: int = Field(default=2, ge=0)
    DOCKER_POSTGRES_HOST: str = Field(default="postgres")
    HH_API_KEY: str = Field(default="fake_hh_api_key")
    CHATGPT_API_KEY: str = Field(default="fake_chatgpt_api_key")
    JWT_SECRET: str = Field(default="secret_jwt")
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_EXPIRES_MINUTES: int = Field(default=1440)

    model_config = SettingsConfigDict(
        env_file=".env",  # default, can be overridden dynamically
        env_file_encoding="utf-8",
    )

    @property
    def DATABASE_DSN(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.DOCKER_POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


def parse_env_file_arg() -> argparse.Namespace:
    """Разбирает аргументы командной строки и возвращает путь к env-файлу."""
    parser = argparse.ArgumentParser(description="FastAPI App")
    parser.add_argument("--env-file", type=str, default=".env")
    return parser.parse_args()


def load_config_from_env_file(env_file: str) -> Config:
    """Загружает конфигурацию приложения из указанного файла окружения."""
    if not Path(env_file).exists():
        raise FileNotFoundError(f"Файл '{env_file}' не найден")

    # Pydantic v2: временно переопределяем env_file через SettingsConfigDict
    class TempConfig(Config):
        model_config = SettingsConfigDict(
            env_file=env_file,
            env_file_encoding="utf-8",
        )

    return TempConfig()


def configure_logging(cfg: Config) -> None:
    """Настраивает систему логирования."""
    numeric_level = getattr(logging, cfg.LOG_LEVEL.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Неверный уровень логирования: {cfg.LOG_LEVEL}")
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def create_app(cfg: Config) -> FastAPI:
    """Фабрика приложения FastAPI."""
    db.engine = create_async_engine(
        cfg.DATABASE_DSN,
        future=True,
        pool_size=cfg.POSTGRES_POOL_SIZE,
        max_overflow=cfg.POSTGRES_IDLE_CONNECTIONS,
        echo=cfg.DEBUG,
    )
    db.session_factory = async_sessionmaker(
        db.engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )

    db.db_context = db.DBContext(session_factory=db.session_factory)

    user_repo.user_repository = user_repo.UserRepository(db_context=db.db_context)

    auth_svc.auth_service = auth_svc.AuthService(
        user_repo=user_repo.user_repository,
        jwt_secret=cfg.JWT_SECRET,
        jwt_algorithm=cfg.JWT_ALGORITHM,
        jwt_expires_minutes=cfg.JWT_EXPIRES_MINUTES,
    )

    auth_router = create_auth_router(svc=auth_svc.auth_service, transaction=db.db_context.transaction)

    api_router = APIRouter(prefix=cfg.API_VERSION)
    api_router.include_router(auth_router)

    @asynccontextmanager
    async def lifespan(app: FastAPI):  # type: ignore
        yield
        if db.engine:
            await db.engine.dispose()

    app = FastAPI(
        title=cfg.APP_NAME,
        description=cfg.APP_DESCRIPTION,
        debug=cfg.DEBUG,
        lifespan=lifespan,
    )
    app.include_router(api_router)

    return app


def run_uvicorn(app: FastAPI, cfg: Config) -> None:
    """Запускает сервер Uvicorn с приложением FastAPI."""
    uvicorn.run(
        app,
        host=cfg.HOST,
        port=cfg.PORT,
        log_level=cfg.LOG_LEVEL.lower(),
        reload=cfg.DEBUG and cfg.WORKERS == 1,
        workers=cfg.WORKERS,
    )

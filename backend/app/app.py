import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from pydantic import BaseSettings, Field
import argparse
import uvicorn

from backend.engines.postgres import PostgresEngine


# Конфигурация приложения
class AppSettings(BaseSettings):
    APP_NAME: str = Field(
        default="FastAPI App", description="Название приложения"
    )
    DEBUG: bool = Field(default=False, description="Включить или отключить режим отладки")
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Уровень логирования"
    )
    HOST: str = Field(default="127.0.0.1", description="Хост для привязки Uvicorn")
    PORT: int = Field(default=8000, description="Порт для привязки Uvicorn")

    # PostgreSQL настройки
    POSTGRES_HOST: str = Field(default="localhost", description="Хост PostgreSQL")
    POSTGRES_PORT: int = Field(default=5432, description="Порт PostgreSQL")
    POSTGRES_DB: str = Field(default="ai_job_agent", description="Имя базы данных")
    POSTGRES_USER: str = Field(default="ai_job_agent_user", description="Пользователь PostgreSQL")
    POSTGRES_PASSWORD: str = Field(default="ai_job_agent_password", description="Пароль PostgreSQL")
    POSTGRES_POOL_SIZE: int = Field(default=10, description="Количество соединений в пуле", ge=1)
    POSTGRES_IDLE_CONNECTIONS: int = Field(default=2, description="Количество простаивающих соединений", ge=0)

    @property
    def DATABASE_DSN(self) -> str:
        """
        Формирует строку подключения к PostgreSQL динамически
        """
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.DOCKER_POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )



# Класс приложения
class App:
    def __init__(self) -> None:
        self.args: argparse.Namespace | None = None
        self.settings: AppSettings | None = None
        self.app: FastAPI | None = None
        self.postgres_engine: PostgresEngine | None = None

    # Разбор аргументов командной строки
    def parse_args(self) -> argparse.Namespace:
        parser = argparse.ArgumentParser(description="FastAPI App с env-файлом")
        parser.add_argument(
            "--env-file", type=str, default=".env", help="Путь к файлу окружения"
        )
        self.args = parser.parse_args()
        return self.args

    # Разбор env-файла
    def parse_envs(self, env_file: str) -> AppSettings:
        if not Path(env_file).exists():
            raise FileNotFoundError(f"Файл окружения '{env_file}' не найден")
        self.settings = AppSettings(model_config={"env_file": env_file})
        return self.settings

    # Настройка логирования
    def configure_logging(self) -> None:
        if self.settings is None:
            raise RuntimeError("Настройки не загружены")
        numeric_level = getattr(logging, self.settings.LOG_LEVEL.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError(f"Неверный уровень логирования: {self.settings.LOG_LEVEL}")
        logging.basicConfig(
            level=numeric_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    # Настройка FastAPI приложения + базы данных (lifespan)
    def configure_app(self) -> FastAPI:
        if self.settings is None:
            raise RuntimeError("Настройки не загружены")

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            await self.postgres_engine.connect()
            try:
                yield
            finally:
                if self.postgres_engine:
                    await self.postgres_engine.dispose()

        self.app = FastAPI(
            title=self.settings.APP_NAME,
            debug=self.settings.DEBUG,
            lifespan=lifespan
        )

        self.postgres_engine = PostgresEngine(
            database_url=self.settings.DATABASE_DSN,
            pool_size=self.settings.DATABASE_POOL_SIZE,
            max_overflow=self.settings.DATABASE_IDLE_CONNECTIONS,
            echo=self.settings.DEBUG,
        )

        return self.app

    # Запуск Uvicorn
    def run_uvicorn(self) -> None:
        if self.app is None or self.settings is None:
            raise RuntimeError("Приложение или настройки не инициализированы")
        uvicorn.run(self.app, host=self.settings.HOST, port=self.settings.PORT)
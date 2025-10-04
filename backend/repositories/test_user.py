from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from backend.engines.db import DBContext
from backend.repositories import user
from backend.repositories.models.user import UserDB


@pytest.mark.asyncio
async def test_save_creates_user_success():
    """Проверка save() при успешном добавлении/обновлении пользователя"""
    now = datetime.now(timezone.utc)

    mock_user = UserDB(
        user_uuid="uuid123",
        username="testuser",
        password_hash="hashed",
        email="test@example.com",
        created_at=now,
        updated_at=now,
    )

    mock_result = MagicMock()
    mock_result.scalar_one.return_value = mock_user

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)

    mock_context = MagicMock(spec=DBContext)
    mock_context.get_session = AsyncMock(return_value=mock_session)

    repo = user.UserRepository(db_context=mock_context)
    result = await repo.save("testuser", "hashed", "test@example.com")

    assert result == {
        "user_uuid": str(mock_user.user_uuid),
        "username": "testuser",
        "email": "test@example.com",
        "created_at": now,
        "updated_at": now,
    }

    mock_session.execute.assert_awaited_once()
    mock_result.scalar_one.assert_called_once()


@pytest.mark.asyncio
async def test_save_returns_none_on_exception():
    """save() возвращает None при ошибке SQLAlchemy"""
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(side_effect=SQLAlchemyError)

    mock_context = MagicMock(spec=DBContext)
    mock_context.get_session = AsyncMock(return_value=mock_session)

    repo = user.UserRepository(db_context=mock_context)
    result = await repo.save("testuser", "hashed", "test@example.com")
    assert result is None
    mock_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_by_username_returns_user():
    """get_by_username() возвращает данные пользователя, если он существует"""
    now = datetime.now(timezone.utc)

    mock_user = UserDB(
        user_uuid="uuid123",
        username="testuser",
        password_hash="hashed",
        email="test@example.com",
        created_at=now,
        updated_at=now,
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)

    mock_context = MagicMock(spec=DBContext)
    mock_context.get_session = AsyncMock(return_value=mock_session)

    repo = user.UserRepository(db_context=mock_context)
    result = await repo.get_by_username("testuser")

    assert result == {
        "user_uuid": str(mock_user.user_uuid),
        "username": "testuser",
        "email": "test@example.com",
        "created_at": now,
        "updated_at": now,
    }

    mock_session.execute.assert_awaited_once()
    mock_result.scalar_one_or_none.assert_called_once()


@pytest.mark.asyncio
async def test_get_by_username_returns_none_if_not_found():
    """get_by_username() возвращает None, если пользователь не найден"""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)

    mock_context = MagicMock(spec=DBContext)
    mock_context.get_session = AsyncMock(return_value=mock_session)

    repo = user.UserRepository(db_context=mock_context)
    result = await repo.get_by_username("missinguser")
    assert result is None

    mock_session.execute.assert_awaited_once()
    mock_result.scalar_one_or_none.assert_called_once()


@pytest.mark.asyncio
async def test_get_by_username_returns_none_on_exception():
    """get_by_username() возвращает None при SQLAlchemyError"""
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(side_effect=SQLAlchemyError)

    mock_context = MagicMock(spec=DBContext)
    mock_context.get_session = AsyncMock(return_value=mock_session)

    repo = user.UserRepository(db_context=mock_context)
    result = await repo.get_by_username("testuser")
    assert result is None
    mock_session.execute.assert_awaited_once()

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from engines import db


@pytest.mark.asyncio
async def test_dbcontext_get_set_current_session():
    """Проверка get_current_session и set_current_session"""
    mock_session = AsyncMock(spec=AsyncSession)
    context = db.DBContext(session_factory=AsyncMock())

    # Изначально сессии нет
    assert context.get_current_session() is None

    # Устанавливаем сессию
    context.set_current_session(mock_session)
    assert context.get_current_session() == mock_session


@pytest.mark.asyncio
async def test_dbcontext_get_session_creates_new_if_none():
    """get_session создаёт новую сессию, если её нет"""
    mock_session = AsyncMock(spec=AsyncSession)
    mock_factory = MagicMock(return_value=mock_session)

    context = db.DBContext(session_factory=mock_factory)

    session = await context.get_session()
    assert session == mock_session
    # Проверяем, что текущая сессия установлена
    assert context.get_current_session() == mock_session
    mock_factory.assert_called_once()


@pytest.mark.asyncio
async def test_dbcontext_get_session_returns_existing():
    """get_session возвращает существующую сессию"""
    mock_session = AsyncMock(spec=AsyncSession)
    context = db.DBContext(session_factory=AsyncMock())
    context.set_current_session(mock_session)

    session = await context.get_session()
    assert session == mock_session

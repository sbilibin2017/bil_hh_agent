import pytest
from unittest.mock import AsyncMock, MagicMock

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from backend.db.db import DBContext


@pytest.mark.asyncio
async def test_get_session_creates_new_session():
    mock_session = AsyncMock(spec=AsyncSession)
    mock_factory = MagicMock(return_value=mock_session)

    db_context = DBContext(async_session_factory=mock_factory)

    session = await db_context.get_session()

    # Ensure factory was called to create session
    mock_factory.assert_called_once()
    # Ensure returned session is the mock session
    assert session is mock_session


@pytest.mark.asyncio
async def test_get_session_reuses_existing_session():
    mock_session = AsyncMock(spec=AsyncSession)
    mock_factory = MagicMock(return_value=mock_session)

    db_context = DBContext(async_session_factory=mock_factory)

    session1 = await db_context.get_session()
    session2 = await db_context.get_session()

    # Factory should be called only once
    mock_factory.assert_called_once()
    # Both calls should return the same session instance
    assert session1 is session2


@pytest.mark.asyncio
async def test_reset_session():
    mock_session = AsyncMock(spec=AsyncSession)
    mock_factory = MagicMock(return_value=mock_session)

    db_context = DBContext(async_session_factory=mock_factory)

    session1 = await db_context.get_session()
    db_context.reset()
    session2 = await db_context.get_session()

    # Factory should be called twice (before and after reset)
    assert mock_factory.call_count == 2
    # After reset, session should be different
    assert session1 is not session2

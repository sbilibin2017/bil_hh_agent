import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import bcrypt
import jwt
import pytest
from fastapi import HTTPException, status

from schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
)
from services.auth import AuthService


@pytest.mark.asyncio
async def test_register_success():
    """Successful user registration"""
    test_uuid = uuid.uuid4()  # generate a valid UUID
    now = datetime.now(timezone.utc)

    mock_user_repo = MagicMock()
    mock_user_repo.get_by_username = AsyncMock(return_value=None)
    mock_user_repo.save = AsyncMock(
        return_value={
            "user_uuid": test_uuid,  # <-- use UUID object, not a random string
            "username": "testuser",
            "email": "test@example.com",
            "created_at": now,
            "updated_at": now,
            "password_hash": "hashed",
        }
    )

    service = AuthService(user_repo=mock_user_repo, jwt_secret="secret")
    request = RegisterRequest(username="testuser", email="test@example.com", password="password")
    response: RegisterResponse = await service.register(request)

    assert isinstance(response, RegisterResponse)
    assert response.user_uuid == test_uuid
    assert response.username == "testuser"
    assert response.email == "test@example.com"
    assert response.created_at == now
    assert response.updated_at == now
    mock_user_repo.get_by_username.assert_awaited_once()
    mock_user_repo.save.assert_awaited_once()


@pytest.mark.asyncio
async def test_register_user_conflict():
    """Регистрация с уже существующим именем пользователя вызывает HTTP 409"""
    mock_user_repo = MagicMock()
    mock_user_repo.get_by_username = AsyncMock(return_value={"username": "testuser"})

    service = AuthService(user_repo=mock_user_repo, jwt_secret="secret")
    request = RegisterRequest(username="testuser", email="test@example.com", password="password")

    with pytest.raises(HTTPException) as exc:
        await service.register(request)

    assert exc.value.status_code == status.HTTP_409_CONFLICT
    assert "уже существует" in exc.value.detail


@pytest.mark.asyncio
async def test_register_save_failure():
    """Регистрация возвращает HTTP 500 при ошибке сохранения"""
    mock_user_repo = MagicMock()
    mock_user_repo.get_by_username = AsyncMock(return_value=None)
    mock_user_repo.save = AsyncMock(return_value=None)

    service = AuthService(user_repo=mock_user_repo, jwt_secret="secret")
    request = RegisterRequest(username="newuser", email="test@example.com", password="password")

    with pytest.raises(HTTPException) as exc:
        await service.register(request)

    assert exc.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
async def test_login_success():
    """Логин успешен, возвращает JWT токен"""
    password = "password"
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    test_uuid = uuid.uuid4()
    mock_user_repo = MagicMock()
    mock_user_repo.get_by_username = AsyncMock(
        return_value={
            "user_uuid": test_uuid,
            "username": "testuser",
            "password_hash": hashed,
        }
    )

    service = AuthService(user_repo=mock_user_repo, jwt_secret="secret", jwt_expires_minutes=60)
    request = LoginRequest(username="testuser", password=password)
    response: LoginResponse = await service.login(request)

    assert isinstance(response, LoginResponse)
    decoded = jwt.decode(response.token, "secret", algorithms=["HS256"])
    # convert UUID to str for comparison
    assert decoded["user_uuid"] == str(test_uuid)
    mock_user_repo.get_by_username.assert_awaited_once()


@pytest.mark.asyncio
async def test_login_user_not_found():
    """Логин с несуществующим пользователем вызывает HTTP 404"""
    mock_user_repo = MagicMock()
    mock_user_repo.get_by_username = AsyncMock(return_value=None)

    service = AuthService(user_repo=mock_user_repo, jwt_secret="secret")
    request = LoginRequest(username="missing", password="pass")

    with pytest.raises(HTTPException) as exc:
        await service.login(request)

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_login_wrong_password():
    """Логин с неверным паролем вызывает HTTP 401"""
    password = "password"
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    test_uuid = uuid.uuid4()
    mock_user_repo = MagicMock()
    mock_user_repo.get_by_username = AsyncMock(
        return_value={
            "user_uuid": test_uuid,
            "username": "testuser",
            "password_hash": hashed,
        }
    )

    service = AuthService(user_repo=mock_user_repo, jwt_secret="secret")
    request = LoginRequest(username="testuser", password="wrongpassword")

    with pytest.raises(HTTPException) as exc:
        await service.login(request)

    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED

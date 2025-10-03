import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient

from backend.routers.auth import create_auth_router
from backend.schemas.auth import RegisterResponse, LoginResponse
from backend.services.auth import AuthService


# ---------------- Fixtures ---------------- #

@pytest.fixture
def mock_auth_service():
    """Mock AuthService with async methods"""
    svc = MagicMock(spec=AuthService)
    svc.register = AsyncMock()
    svc.login = AsyncMock()
    return svc


@pytest.fixture
def mock_transaction():
    """Mock transaction decorator to just return the function unchanged"""

    def decorator(func):
        return func

    return decorator


@pytest.fixture
def app(mock_auth_service, mock_transaction):
    """FastAPI app with auth router included"""
    app = FastAPI()
    app.include_router(create_auth_router(mock_auth_service, transaction=mock_transaction))
    return app


# ---------------- Tests ---------------- #

def test_register_success(app, mock_auth_service):
    """Successful user registration"""
    import uuid
    from datetime import datetime, timezone

    test_uuid = uuid.uuid4()
    now = datetime.now(timezone.utc)

    mock_auth_service.register.return_value = RegisterResponse(
        user_uuid=test_uuid,
        username="testuser",
        email="test@example.com",
        created_at=now,
        updated_at=now,
    )

    payload = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    }
    client = TestClient(app)
    response = client.post("/auth/register", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    mock_auth_service.register.assert_awaited_once()


def test_register_conflict(app, mock_auth_service):
    """Registration fails if username exists"""
    mock_auth_service.register.side_effect = HTTPException(
        status_code=status.HTTP_409_CONFLICT, detail="Username exists"
    )

    payload = {
        "username": "existinguser",
        "email": "existing@example.com",
        "password": "password123"
    }
    client = TestClient(app)
    response = client.post("/auth/register", json=payload)

    assert response.status_code == 409
    assert response.json()["detail"] == "Username exists"


def test_login_success(app, mock_auth_service):
    """Successful login returns JWT token"""
    mock_auth_service.login.return_value = LoginResponse(token="fake_jwt_token")

    payload = {"username": "testuser", "password": "password123"}
    client = TestClient(app)
    response = client.post("/auth/login", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["token"] == "fake_jwt_token"
    mock_auth_service.login.assert_awaited_once()


def test_login_not_found(app, mock_auth_service):
    """Login fails if user does not exist"""
    mock_auth_service.login.side_effect = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
    )

    payload = {"username": "unknown", "password": "password123"}
    client = TestClient(app)
    response = client.post("/auth/login", json=payload)

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_login_unauthorized(app, mock_auth_service):
    """Login fails if password is incorrect"""
    mock_auth_service.login.side_effect = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password"
    )

    payload = {"username": "testuser", "password": "wrongpassword"}
    client = TestClient(app)
    response = client.post("/auth/login", json=payload)

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid password"

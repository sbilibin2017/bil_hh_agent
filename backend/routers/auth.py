from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from backend.services.auth import (
    AuthError,
    AuthService,
    InvalidPasswordError,
    UserAlreadyExistsError,
    UserNotFoundError,
)


# ----------------------------
# Request / Response models
# ----------------------------
class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str


# ----------------------------
# Router factory with closures
# ----------------------------
def create_auth_router(svc: AuthService) -> APIRouter:
    """
    Create an APIRouter using closures to capture AuthService.
    """
    router = APIRouter(prefix="/auth", tags=["auth"])

    @router.post("/register", response_model=None)
    async def register_handler(data: RegisterRequest):
        try:
            await svc.register(username=data.username, email=data.email, password=data.password)
            return {"message": "User registered successfully"}
        except UserAlreadyExistsError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already exists",
            )
        except AuthError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to register user",
            )

    @router.post("/login", response_model=LoginResponse)
    async def login_handler(data: LoginRequest):
        try:
            token = await svc.login(username=data.username, password=data.password)
            return LoginResponse(token=token)
        except UserNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        except InvalidPasswordError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )
        except AuthError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to login",
            )

    return router

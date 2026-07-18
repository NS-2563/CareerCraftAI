from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.user.models import User
from app.user.schemas import (
    LoginRequest,
    RegisterRequest,
    Token,
    UserResponse,
    GoogleOAuthRequest,
    GoogleOAuthResponse,
)
from app.auth.service import AuthService, GoogleOAuthService
from app.utils.response import success_response
from app.utils.exceptions import AppException

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user."""
    user, token = AuthService.register(db, user_data)
    return user


@router.post("/login", response_model=Token)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """Login with email and password."""
    user, token = AuthService.login(db, credentials.email, credentials.password)
    return token

@router.post("/token", response_model=Token)
def oauth2_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    OAuth2 Password Flow endpoint.
    Used by Swagger UI.
    """

    user, token = AuthService.login(
        db=db,
        email=form_data.username,
        password=form_data.password,
    )

    return token


@router.post("/refresh", response_model=Token)
def refresh_token(refresh_token: str):
    """Refresh access token using refresh token."""
    token = AuthService.refresh_token(refresh_token)
    return token


@router.get("/me", response_model=UserResponse)
def get_current_user(current_user: User = Depends(get_current_active_user)):
    """Get current user profile."""
    return current_user


# Google OAuth endpoints (placeholder)
@router.get("/google/url")
def get_google_auth_url():
    """Get Google OAuth authorization URL."""
    raise AppException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        message="Google OAuth not yet implemented",
    )


@router.post("/google/callback", response_model=GoogleOAuthResponse)
def google_callback(auth_request: GoogleOAuthRequest, db: Session = Depends(get_db)):
    """Exchange Google OAuth code for tokens."""
    raise AppException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        message="Google OAuth not yet implemented",
    )
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_active_user
from app.main import limiter
from app.models.user import User
from app.schemas.user import (
    LoginRequest,
    RegisterRequest,
    RefreshRequest,
    Token,
    LogoutResponse,
    UserResponse,
    GoogleOAuthRequest,
    GoogleOAuthResponse,
)
from app.services.auth_service import AuthService, GoogleOAuthService
from app.utils.response import success_response
from app.utils.exceptions import AppException

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_REGISTER)
def register(request: Request, user_data: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user."""
    user, token = AuthService.register(db, user_data)
    return user


@router.post("/login", response_model=Token)
@limiter.limit(settings.RATE_LIMIT_LOGIN)
def login(request: Request, credentials: LoginRequest, db: Session = Depends(get_db)):
    """Login with email and password."""
    user, token = AuthService.login(db, credentials.email, credentials.password)
    return token

@router.post("/token", response_model=Token)
@limiter.limit(settings.RATE_LIMIT_LOGIN)
def oauth2_login(
    request: Request,
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
@limiter.limit(settings.RATE_LIMIT_REFRESH)
def refresh_token(
    request: Request,
    body: RefreshRequest,
    db: Session = Depends(get_db),
):
    """Refresh access token using refresh token.

    The refresh token must be sent in the POST request body.
    On success, old refresh token is invalidated (rotation).
    """
    token = AuthService.refresh_token(db, body.refresh_token)
    return token


@router.post("/logout", response_model=LogoutResponse)
def logout(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Logout user and invalidate all existing tokens server-side."""
    AuthService.logout(current_user, db)
    return LogoutResponse(message="Logged out successfully")


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
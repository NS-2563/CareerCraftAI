from fastapi import APIRouter, Depends, Request, Response, status
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


def _is_dev() -> bool:
    """Heuristic: localhost origins imply a development environment."""
    return "localhost" in settings.CORS_ORIGINS


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    """Set the refresh token as an httpOnly cookie.

    Secure flag is omitted in local dev (HTTP); applied in production (HTTPS).
    SameSite=Lax allows the cookie to be sent on navigations from the same
    registrable domain; the frontend and backend share localhost so this is
    same-site despite different ports.
    """
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=not _is_dev(),
        samesite="lax",
        path="/api/auth/refresh",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )


def _clear_refresh_cookie(response: Response) -> None:
    """Expire the refresh-token cookie immediately."""
    response.set_cookie(
        key="refresh_token",
        value="",
        httponly=True,
        secure=not _is_dev(),
        samesite="lax",
        path="/api/auth/refresh",
        max_age=0,
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_REGISTER)
def register(request: Request, user_data: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user."""
    user, token = AuthService.register(db, user_data)
    return user


@router.post("/login", response_model=Token)
@limiter.limit(settings.RATE_LIMIT_LOGIN)
def login(
    request: Request,
    credentials: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    """Login with email and password.

    The refresh token is returned as an httpOnly cookie instead of in the
    JSON body.  Only the short-lived access token appears in the response.
    """
    user, token = AuthService.login(db, credentials.email, credentials.password)
    _set_refresh_cookie(response, token.refresh_token)
    return Token(access_token=token.access_token, token_type=token.token_type)


@router.post("/token", response_model=Token)
@limiter.limit(settings.RATE_LIMIT_LOGIN)
def oauth2_login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    OAuth2 Password Flow endpoint.
    Used by Swagger UI — returns both tokens in JSON for compatibility.
    """

    user, token = AuthService.login(
        db=db,
        email=form_data.username,
        password=form_data.password,
    )

    # Also set the cookie so the frontend can benefit from cookie auth
    # even when using the Swagger login button.
    _set_refresh_cookie(response, token.refresh_token)
    return token


@router.post("/refresh", response_model=Token)
@limiter.limit(settings.RATE_LIMIT_REFRESH)
def refresh_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Refresh access token using the httpOnly cookie.

    The refresh token is read from the ``refresh_token`` cookie rather than
    from the request body.  A new rotated refresh token is set on the cookie
    and the old one is invalidated server-side.
    """
    refresh_token_value = request.cookies.get("refresh_token")
    if not refresh_token_value:
        from app.utils.exceptions import UnauthorizedException
        raise UnauthorizedException("No refresh token cookie present")

    token = AuthService.refresh_token(db, refresh_token_value)
    _set_refresh_cookie(response, token.refresh_token)
    return Token(access_token=token.access_token, token_type=token.token_type)


@router.post("/logout", response_model=LogoutResponse)
def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Logout user, invalidate tokens server-side, and clear the cookie."""
    AuthService.logout(current_user, db)
    _clear_refresh_cookie(response)
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
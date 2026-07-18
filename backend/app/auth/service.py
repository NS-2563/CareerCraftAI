from datetime import timedelta
from sqlalchemy.orm import Session

from app.core.config import settings
from app.user.models import User
from app.core.dependencies import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.user.schemas import Token, UserCreate, UserResponse
from app.utils.exceptions import (
    NotFoundException,
    ConflictException,
    UnauthorizedException,
)


class AuthService:
    """Service for authentication operations."""

    @staticmethod
    def register(db: Session, user_data: UserCreate) -> tuple[User, Token]:
        """Register a new user."""
        # Check if user exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise ConflictException("Email already registered")

        existing_username = db.query(User).filter(User.username == user_data.username).first()
        if existing_username:
            raise ConflictException("Username already taken")

        # Create user
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        # Create tokens
        token = AuthService._create_tokens(db_user.id)

        return db_user, token

    @staticmethod
    def login(db: Session, email: str, password: str) -> tuple[User, Token]:
        """Authenticate and login user."""
        user = db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.hashed_password):
            raise UnauthorizedException("Invalid email or password")

        if not user.is_active:
            raise UnauthorizedException("User account is disabled")

        token = AuthService._create_tokens(user.id)

        return user, token

    @staticmethod
    def refresh_token(refresh_token_value: str) -> Token:
        """Refresh access token using refresh token."""
        payload = decode_token(refresh_token_value)
        if not payload or payload.get("type") != "refresh":
            raise UnauthorizedException("Invalid refresh token")

        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedException("Invalid token payload")

        token = AuthService._create_tokens(int(user_id))

        return token

    @staticmethod
    def _create_tokens(user_id: int) -> Token:
        """Create access and refresh tokens."""
        access_token = create_access_token(
            data={"sub": str(user_id)},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        refresh_token_value = create_refresh_token(data={"sub": str(user_id)})

        return Token(
            access_token=access_token,
            refresh_token=refresh_token_value,
            token_type="bearer",
        )

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> User:
        """Get user by ID."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundException("User", str(user_id))
        return user

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> User:
        """Get user by email."""
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise NotFoundException("User", email)
        return user


# Google OAuth placeholder functions
class GoogleOAuthService:
    """Service for Google OAuth operations (placeholder)."""

    @staticmethod
    def get_authorization_url() -> str:
        """Get Google OAuth authorization URL."""
        # Placeholder - would implement actual Google OAuth
        raise NotImplementedError("Google OAuth not yet implemented")

    @staticmethod
    def exchange_code(code: str, db: Session) -> tuple[User, Token]:
        """Exchange authorization code for tokens."""
        # Placeholder - would implement actual Google OAuth
        raise NotImplementedError("Google OAuth not yet implemented")

    @staticmethod
    def get_user_info(access_token: str) -> dict:
        """Get user info from Google."""
        # Placeholder - would implement actual Google OAuth
        raise NotImplementedError("Google OAuth not yet implemented")
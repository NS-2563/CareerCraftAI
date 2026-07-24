from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


DEFAULT_INSECURE_KEYS = {
    "your-secret-key-change-in-production",
    "change-this-to-a-random-secret-key",
    "secret",
    "default",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    # Database
    DATABASE_URL: str = "sqlite:///./careercraft.db"

    # JWT Authentication
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Google OAuth (placeholder)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173"

    # AI Provider Configuration
    AI_PROVIDER: str = "gemini"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


settings = Settings()

# Security check: refuse to run with a known insecure SECRET_KEY
if settings.SECRET_KEY in DEFAULT_INSECURE_KEYS:
    raise RuntimeError(
        "SECURITY: SECRET_KEY is set to a known insecure default value. "
        "Generate a strong random key and set it in your .env file.\n"
        "  python -c \"import secrets; print(secrets.token_urlsafe(64))\""
    )
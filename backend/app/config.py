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

    # Test environment — set to True by the test harness (e.g. via the TESTING
    # env var in tests/conftest.py). When True the slowapi Limiter is built
    # disabled so the real production rate limits never collide across the
    # automated suite. Production is completely unaffected because it runs with
    # TESTING=False (the default) and therefore keeps the limiter enabled.
    TESTING: bool = False

    # Database
    DATABASE_URL: str = "sqlite:///./careercraft.db"

    # JWT Authentication
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Rate limiting — unauthenticated endpoints (IP-based)
    RATE_LIMIT_LOGIN: str = "10/minute"
    RATE_LIMIT_REGISTER: str = "5/minute"
    RATE_LIMIT_REFRESH: str = "30/minute"
    RATE_LIMIT_CHANGE_PASSWORD: str = "5/minute"

    # Rate limiting — AI endpoints (per-user burst + daily quota)
    # Relatively high defaults for tests; production should tighten via .env
    RATE_LIMIT_ANALYSIS: str = "60/minute"
    RATE_LIMIT_ANALYSIS_DAILY: str = "200/day"
    RATE_LIMIT_JD_MATCH: str = "60/minute"
    RATE_LIMIT_JD_MATCH_DAILY: str = "200/day"
    RATE_LIMIT_AI: str = "60/minute"
    RATE_LIMIT_AI_DAILY: str = "200/day"
    RATE_LIMIT_COVER_LETTER: str = "30/minute"
    RATE_LIMIT_COVER_LETTER_DAILY: str = "100/day"
    RATE_LIMIT_COMMUNICATION: str = "30/minute"
    RATE_LIMIT_COMMUNICATION_DAILY: str = "100/day"
    RATE_LIMIT_CAREER_COACH: str = "20/minute"
    RATE_LIMIT_CAREER_COACH_DAILY: str = "50/day"
    RATE_LIMIT_INTERVIEW_PREP: str = "30/minute"
    RATE_LIMIT_INTERVIEW_PREP_DAILY: str = "100/day"
    RATE_LIMIT_INTERVIEW_EVAL: str = "60/minute"
    RATE_LIMIT_INTERVIEW_EVAL_DAILY: str = "200/day"

    # Account lockout
    MAX_FAILED_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_MINUTES: int = 15

    # Google OAuth (placeholder)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173"

    # AI Provider Configuration
    AI_PROVIDER: str = "gemini"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # Suggestions
    SUGGESTION_FOLLOW_UP_DAYS: int = 7

    # Internal job trigger secret — shared secret that an external scheduler
    # (Render Cron Jobs / scheduled GitHub Actions workflow) must send in the
    # X-Internal-Secret header to call POST /api/internal/run-daily-suggestions.
    # This is NOT the user JWT; it authenticates machine-to-machine calls only.
    # When empty the endpoint fails closed (503) until configured in production.
    INTERNAL_JOB_SECRET: str = ""

    # Communication thread-summary overdue rule: the conversation is flagged
    # "response overdue" when the most recent message is inbound and MORE than
    # this many whole days have passed with no outbound reply (strictly >).
    COMMUNICATION_OVERDUE_AFTER_DAYS: int = 5

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
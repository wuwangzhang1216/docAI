from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database (默认使用 SQLite 进行本地开发)
    DATABASE_URL: str = "sqlite+aiosqlite:///./xinshoucai.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # S3 / MinIO
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET: str = "xinshoucai"

    # Authentication
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    ALGORITHM: str = "HS256"
    DEFAULT_PATIENT_PASSWORD: str = "Welcome123!"  # Default password for doctor-created patients

    # AI - Anthropic
    ANTHROPIC_API_KEY: str = ""

    # Application
    DEBUG: bool = True
    APP_NAME: str = "心守AI"
    API_V1_PREFIX: str = "/api/v1"

    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30  # seconds

    # File Upload
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB

    # Email Settings
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = False
    SMTP_START_TLS: bool = True

    EMAIL_FROM: str = "noreply@xinshoucai.com"
    EMAIL_FROM_NAME: str = "心守AI"

    # Frontend URL (for email links)
    FRONTEND_URL: str = "http://localhost:3000"

    # Email Feature Flags
    EMAIL_ENABLED: bool = True
    EMAIL_RISK_ALERTS_ENABLED: bool = True

    # Email Queue Settings
    EMAIL_MAX_RETRIES: int = 3
    EMAIL_RETRY_DELAY_BASE: int = 60  # seconds

    # Password Reset Settings
    PASSWORD_RESET_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()

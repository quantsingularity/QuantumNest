import os
import secrets
from enum import Enum
from functools import lru_cache
from typing import Dict, List, Optional

from pydantic import BaseSettings, validator


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Settings(BaseSettings):
    """
    Enhanced application settings with comprehensive configuration support

    This class centralizes all configuration settings for the application
    and supports loading from environment variables with validation and defaults.
    """

    # Environment settings
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    DEBUG: bool = False

    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "QuantumNest Capital API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Advanced Financial Platform with AI-Powered Analytics"

    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1

    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    PASSWORD_MIN_LENGTH: int = 8
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 30

    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./quantumnest.db")
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 3600

    # Redis settings
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    REDIS_DB: int = 0

    # Celery settings
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv(
        "CELERY_RESULT_BACKEND", "redis://localhost:6379/0"
    )
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: List[str] = ["json"]
    CELERY_TIMEZONE: str = "UTC"
    CELERY_ENABLE_UTC: bool = True

    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]  # In production, replace with specific origins
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 100
    RATE_LIMIT_BURST: int = 200

    # AI model settings
    AI_MODELS_DIR: str = os.getenv("AI_MODELS_DIR", "./models")
    AI_MODEL_CACHE_SIZE: int = 5
    AI_PREDICTION_TIMEOUT: int = 30
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    HUGGINGFACE_API_KEY: Optional[str] = os.getenv("HUGGINGFACE_API_KEY")

    # Financial data providers
    ALPHA_VANTAGE_API_KEY: Optional[str] = os.getenv("ALPHA_VANTAGE_API_KEY")
    YAHOO_FINANCE_ENABLED: bool = True
    QUANDL_API_KEY: Optional[str] = os.getenv("QUANDL_API_KEY")
    IEX_CLOUD_API_KEY: Optional[str] = os.getenv("IEX_CLOUD_API_KEY")

    # Blockchain settings
    ETHEREUM_RPC_URL: str = os.getenv("ETHEREUM_RPC_URL", "http://localhost:8545")
    POLYGON_RPC_URL: str = os.getenv("POLYGON_RPC_URL", "https://polygon-rpc.com")
    BSC_RPC_URL: str = os.getenv("BSC_RPC_URL", "https://bsc-dataseed.binance.org")
    PRIVATE_KEY: Optional[str] = os.getenv("PRIVATE_KEY")
    CONTRACT_ADDRESSES: Dict[str, str] = {}

    # Logging settings
    LOG_LEVEL: LogLevel = LogLevel.INFO
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[str] = os.getenv("LOG_FILE")
    LOG_MAX_SIZE: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5

    # Monitoring and metrics
    METRICS_ENABLED: bool = True
    HEALTH_CHECK_INTERVAL: int = 30
    PROMETHEUS_ENABLED: bool = False
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN")

    # Email settings
    SMTP_HOST: Optional[str] = os.getenv("SMTP_HOST")
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD")
    SMTP_TLS: bool = True
    EMAIL_FROM: Optional[str] = os.getenv("EMAIL_FROM")

    # File storage
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: List[str] = [".pdf", ".csv", ".xlsx", ".json"]

    # Feature flags
    ENABLE_REGISTRATION: bool = True
    ENABLE_EMAIL_VERIFICATION: bool = False
    ENABLE_TWO_FACTOR_AUTH: bool = False
    ENABLE_SOCIAL_LOGIN: bool = False
    ENABLE_ADVANCED_ANALYTICS: bool = True
    ENABLE_REAL_TIME_UPDATES: bool = True

    # Performance settings
    CACHE_TTL: int = 300  # 5 minutes
    MAX_CONCURRENT_REQUESTS: int = 100
    REQUEST_TIMEOUT: int = 30

    @validator("SECRET_KEY")
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v

    @validator("PASSWORD_MIN_LENGTH")
    def validate_password_length(cls, v):
        if v < 8:
            raise ValueError("PASSWORD_MIN_LENGTH must be at least 8")
        return v

    @validator("CORS_ORIGINS")
    def validate_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True
        use_enum_values = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings with caching

    Returns a cached instance of the Settings class to avoid
    reloading environment variables on each call.
    """
    return Settings()


# Environment-specific configurations
def get_database_url(settings: Settings) -> str:
    """Get database URL based on environment"""
    if settings.ENVIRONMENT == Environment.PRODUCTION:
        return settings.DATABASE_URL
    elif settings.ENVIRONMENT == Environment.STAGING:
        return settings.DATABASE_URL.replace("quantumnest.db", "quantumnest_staging.db")
    else:
        return settings.DATABASE_URL.replace("quantumnest.db", "quantumnest_dev.db")


def is_production() -> bool:
    """Check if running in production environment"""
    return get_settings().ENVIRONMENT == Environment.PRODUCTION


def is_development() -> bool:
    """Check if running in development environment"""
    return get_settings().ENVIRONMENT == Environment.DEVELOPMENT

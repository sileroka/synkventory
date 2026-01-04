"""
Application configuration settings.

All settings are read from environment variables with sensible defaults
for local development. In production, configure via environment variables
or a .env file.
"""

import secrets
from typing import List, Optional, Union

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ==========================================================================
    # Application Settings
    # ==========================================================================
    PROJECT_NAME: str = "Synkventory API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False

    # Secret key for JWT tokens and other cryptographic operations
    # In production, set this to a secure random string
    SECRET_KEY: str = secrets.token_urlsafe(32)

    # ==========================================================================
    # Database Settings
    # ==========================================================================
    # Digital Ocean and other PaaS providers supply DATABASE_URL directly
    # If DATABASE_URL is set, it takes precedence over individual settings
    DATABASE_URL: Optional[str] = None

    # Individual database settings (used if DATABASE_URL is not set)
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_SERVER: str = "db"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "synkventory"

    # Database connection pool settings
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30

    # ==========================================================================
    # CORS Settings
    # ==========================================================================
    # Comma-separated list of allowed origins
    # Example: "http://localhost:4200,https://app.synkventory.com"
    CORS_ORIGINS: str = "http://localhost:4200,http://localhost"

    # Cookie domain for cross-subdomain auth
    # Set to ".synkventory.com" in production to share cookies across subdomains
    COOKIE_DOMAIN: Optional[str] = None

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def validate_cors_origins(cls, v: Union[str, List[str]]) -> str:
        """Ensure CORS_ORIGINS is stored as a string."""
        if isinstance(v, list):
            return ",".join(v)
        return v

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS into a list of URLs."""
        if not self.CORS_ORIGINS:
            return []
        return [
            origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()
        ]

    # ==========================================================================
    # Server Settings
    # ==========================================================================
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1

    # ==========================================================================
    # Logging Settings
    # ==========================================================================
    LOG_LEVEL: str = "INFO"

    # ==========================================================================
    # DigitalOcean Spaces Settings (S3-compatible storage)
    # ==========================================================================
    SPACES_ACCESS_KEY: Optional[str] = None
    SPACES_SECRET_KEY: Optional[str] = None
    SPACES_BUCKET: str = "synkventory-storage"
    SPACES_REGION: str = "sfo3"
    SPACES_ENDPOINT: Optional[str] = None

    # Signed URL expiration in seconds (default 1 hour)
    SPACES_URL_EXPIRATION: int = 3600

    # Max file size in bytes (default 10MB)
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024

    # Allowed image types
    ALLOWED_IMAGE_TYPES: str = "image/jpeg,image/png,image/gif,image/webp"

    @property
    def spaces_endpoint_url(self) -> str:
        """Get the Spaces endpoint URL."""
        if self.SPACES_ENDPOINT:
            return self.SPACES_ENDPOINT
        return f"https://{self.SPACES_REGION}.digitaloceanspaces.com"

    @property
    def allowed_image_types_list(self) -> list:
        """Get allowed image types as a list."""
        return [t.strip() for t in self.ALLOWED_IMAGE_TYPES.split(",")]

    # ==========================================================================
    # Database URL Property
    # ==========================================================================
    @property
    def database_url(self) -> str:
        """
        Get the database URL.

        If DATABASE_URL is set (e.g., from Digital Ocean), use it directly.
        Otherwise, construct from individual settings.

        Digital Ocean provides URLs in the format:
        postgresql://user:password@host:port/database?sslmode=require
        """
        if self.DATABASE_URL:
            # Digital Ocean and Heroku use 'postgres://' but SQLAlchemy needs 'postgresql://'
            url = self.DATABASE_URL
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql://", 1)
            return url

        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def async_database_url(self) -> str:
        """Get async database URL for asyncpg driver."""
        url = self.database_url
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)


settings = Settings()

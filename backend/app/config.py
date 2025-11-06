"""Application configuration using pydantic settings."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App
    APP_NAME: str = "FinanceHub"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql://financehub_user:financehub_password@localhost:5432/financehub"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ENCRYPTION_KEY: str = "your-32-char-encryption-key-here!"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # VTB Open Banking
    VTB_API_BASE_URL: str = "https://ift.rtuitlab.dev"
    VTB_TEAM_ID: str = "team075"
    VTB_TEAM_SECRET: str = "1IbEJkXNjswkQLNCqZiYW4mgVSvuC8Di"
    
    # GOST Configuration
    USE_GOST: bool = False
    GOST_API_BASE: str = "https://api.gost.bankingapi.ru:8443"
    
    # Banking API URLs
    BANKING_API_URL: str = "https://api.bankingapi.ru"
    AUTH_API_URL: str = "https://auth.bankingapi.ru/auth/realms/kubernetes/protocol/openid-connect/token"
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS_ORIGINS from comma-separated string to list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore"  # Ignore extra fields from .env
    }


settings = Settings()

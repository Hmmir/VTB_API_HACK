"""Application configuration."""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    APP_NAME: str = "FinanceHub API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # OpenBanking Russia Sandbox
    VTB_TEAM_ID: str = ""  # Your client_id from HackAPI platform
    VTB_TEAM_SECRET: str = ""  # Your client_secret from HackAPI platform
    
    # GOST Gateway Support
    USE_GOST: bool = False  # Enable GOST-compliant TLS connection
    GOST_API_BASE: str = "https://api.gost.bankingapi.ru:8443"
    GOST_AUTH_URL: str = "https://auth.bankingapi.ru/auth/realms/kubernetes/protocol/openid-connect/token"
    
    # Non-GOST API (regular sandbox)
    OPENBANKING_API_BASE: str = "https://api.bankingapi.ru"
    
    # Bank URLs (OpenBanking Russia Sandbox)
    # If USE_GOST=True, will use GOST_API_BASE instead
    VBANK_API_URL: str = "https://vbank.open.bankingapi.ru"
    ABANK_API_URL: str = "https://abank.open.bankingapi.ru"
    SBANK_API_URL: str = "https://sbank.open.bankingapi.ru"
    
    # Default bank for demo
    DEFAULT_BANK: str = "vbank"
    
    # Encryption
    ENCRYPTION_KEY: str
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    
    # Cache
    CACHE_TTL: int = 3600  # 1 hour
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"


settings = Settings()


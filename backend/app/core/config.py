"""
Core configuration for the application.
"""

import os
from typing import List, Union, Dict, Set, Optional, Tuple, Type
from pydantic_settings import BaseSettings, SettingsConfigDict
import pydantic_settings
from pydantic import AnyHttpUrl, validator, EmailStr, Field
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings."""
    # Application Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Austin Property Listing API"
    DEBUG: bool = False
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # CORS - Read as plain string, parse later
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8080,http://127.0.0.1:*"
    
    # Comment out validator (no longer needed for string)
    # @validator("CORS_ORIGINS", pre=True, always=True)
    # def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
    #     if isinstance(v, str):
    #         # If it's a string, assume comma-separated
    #         return [i.strip() for i in v.split(",") if i.strip()]
    #     # If it's already a list (e.g., from default), return as is
    #     return v
        
    # API Security
    SENSITIVE_HEADERS: Set[str] = {
        "authorization", 
        "x-api-key", 
        "cookie", 
        "session", 
        "x-csrf-token",
        "supabase-auth-token",
        "stripe-signature"
    }
    
    # Rate Limiting
    DEFAULT_RATE_LIMIT: int = int(os.getenv("DEFAULT_RATE_LIMIT", "100"))  # 100 reqs/min
    READ_RATE_LIMIT: int = int(os.getenv("READ_RATE_LIMIT", "300"))        # 300 reqs/min
    WRITE_RATE_LIMIT: int = int(os.getenv("WRITE_RATE_LIMIT", "60"))       # 60 reqs/min
    PROPERTIES_RATE_LIMIT: int = int(os.getenv("PROPERTIES_RATE_LIMIT", "500"))  # 500 reqs/min
    ADMIN_RATE_LIMIT: int = int(os.getenv("ADMIN_RATE_LIMIT", "30"))      # 30 reqs/min
    
    # Supabase
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_JWT_SECRET: str
    
    # Neo4j
    NEO4J_URI: str
    NEO4J_USERNAME: str
    NEO4J_PASSWORD: str
    NEO4J_DATABASE: str = "neo4j"
    
    # Redis
    REDIS_URL: str
    
    # Celery
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    
    # Email Scraping
    EMAIL_HOST: str
    EMAIL_PORT: int
    EMAIL_USERNAME: str
    EMAIL_PASSWORD: str
    EMAIL_USE_SSL: bool = True
    
    # SendGrid
    SENDGRID_API_KEY: str
    SENDGRID_FROM_EMAIL: str
    SENDGRID_FROM_NAME: str
    SENDGRID_TEMPLATES_WELCOME_ID: str
    SENDGRID_TEMPLATES_PASSWORD_RESET_ID: str
    SENDGRID_TEMPLATES_PROPERTY_UPDATE_ID: str
    SENDGRID_TEMPLATES_MISSING_INFO_REQUEST_ID: str
    
    # Stripe
    STRIPE_PUBLISHABLE_KEY: str
    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    STRIPE_MONTHLY_PRICE_ID: str
    STRIPE_ANNUAL_PRICE_ID: str
    STRIPE_CURRENCY: str = "usd"
    
    # Web Scraping
    SCRAPER_USER_AGENT: str = os.getenv(
        "SCRAPER_USER_AGENT", 
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
    )
    SCRAPER_TIMEOUT: int = int(os.getenv("SCRAPER_TIMEOUT", "60"))
    PLAYWRIGHT_HEADLESS: bool = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() == "true"
    
    # MCP Server Configuration
    MCP_SERVER_TYPE: str = os.getenv("MCP_SERVER_TYPE", "firecrawl")
    MCP_FIRECRAWL_URL: str = os.getenv("MCP_FIRECRAWL_URL", "http://localhost:3000")
    MCP_PLAYWRIGHT_URL: str = os.getenv("MCP_PLAYWRIGHT_URL", "http://localhost:3001")
    MCP_PUPPETEER_URL: str = os.getenv("MCP_PUPPETEER_URL", "http://localhost:3002")
    MCP_MAX_CONCURRENT_SESSIONS: int = int(os.getenv("MCP_MAX_CONCURRENT_SESSIONS", "5"))
    MCP_REQUEST_TIMEOUT: int = int(os.getenv("MCP_REQUEST_TIMEOUT", "60"))
    MCP_ENABLE_LLM_GUIDANCE: bool = os.getenv("MCP_ENABLE_LLM_GUIDANCE", "false").lower() == "true"
    MCP_LLM_PROVIDER: str = os.getenv("MCP_LLM_PROVIDER", "openai")
    MCP_LLM_MODEL: str = os.getenv("MCP_LLM_MODEL", "gpt-3.5-turbo")
    
    # Socket.IO
    SOCKETIO_PATH: str = "/socket.io"
    SOCKETIO_CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3002"
    
    # @validator("SOCKETIO_CORS_ORIGINS", pre=True)
    # def assemble_socketio_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
    #     if isinstance(v, str) and not v.startswith("["):
    #         return [i.strip() for i in v.split(",")]
    #     elif isinstance(v, (list, str)):
    #         return v
    #     raise ValueError(v)
    
    # Sentry
    SENTRY_DSN: str = ""
    SENTRY_ENVIRONMENT: str = "development"
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1
    
    # Authentication
    AUTH_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Map Configuration
    DEFAULT_MAP_CENTER_LAT: float = 30.2672
    DEFAULT_MAP_CENTER_LNG: float = -97.7431
    DEFAULT_MAP_ZOOM: int = 12
    
    # Feature Flags
    ENABLE_REAL_TIME_UPDATES: bool = True
    ENABLE_EMAIL_SCRAPING: bool = True
    ENABLE_WEB_SCRAPING: bool = True
    ENABLE_OCR_PROCESSING: bool = True
    ENABLE_ADMIN_FEATURES: bool = True
    ENABLE_EMAIL_NOTIFICATIONS: bool = True
    ENABLE_PAYMENT_SYSTEM: bool = True
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    
    class Config:
        # Explicitly set env_file path relative to this config file
        # Go up one level (core -> app) then to backend/.env
        env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
        case_sensitive = True
        extra = 'ignore'
        _env_file_encoding = 'utf-8'

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: pydantic_settings.sources.InitSettingsSource,
        env_settings: pydantic_settings.sources.EnvSettingsSource,
        dotenv_settings: pydantic_settings.sources.DotEnvSettingsSource,
        file_secret_settings: pydantic_settings.sources.SecretsSettingsSource,
    ) -> Tuple[pydantic_settings.sources.DotEnvSettingsSource, pydantic_settings.sources.InitSettingsSource]:
        """Explicitly use only DotEnv and Init sources."""
        # Ensure the .env file path is correct relative to the execution context
        # Since we run from `backend`, it should find `.env`
        return dotenv_settings, init_settings

# Create settings instance
settings = Settings() 
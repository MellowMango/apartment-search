import os
from typing import List, Union
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, validator

class Settings(BaseSettings):
    # Application Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Austin Multifamily Property Listing Map"
    DEBUG: bool = False
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
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
    SCRAPER_USER_AGENT: str
    SCRAPER_TIMEOUT: int = 30
    PLAYWRIGHT_HEADLESS: bool = True
    
    # MCP Server Configuration
    FIRECRAWL_API_KEY: str = ""
    FIRECRAWL_API_URL: str = "https://api.firecrawl.dev"
    MCP_SERVER_TYPE: str = "firecrawl"  # Options: firecrawl, playwright, puppeteer
    MCP_PLAYWRIGHT_URL: str = "http://localhost:3001"
    MCP_PUPPETEER_URL: str = "http://localhost:3002"
    MCP_MAX_CONCURRENT_SESSIONS: int = 5
    MCP_REQUEST_TIMEOUT: int = 60
    MCP_ENABLE_LLM_GUIDANCE: bool = True
    MCP_LLM_PROVIDER: str = "openai"
    MCP_LLM_MODEL: str = "gpt-4"
    MCP_LLM_API_KEY: str = ""
    
    # Socket.IO
    SOCKETIO_PATH: str = "/socket.io"
    SOCKETIO_CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    @validator("SOCKETIO_CORS_ORIGINS", pre=True)
    def assemble_socketio_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
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
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings() 
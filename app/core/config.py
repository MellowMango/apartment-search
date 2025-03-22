import os
import secrets
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    PROJECT_NAME: str = "Acquire Apartments API"
    DEBUG: bool = False
    
    # CORS will be loaded directly from environment variables
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    SOCKETIO_CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Supabase
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str  # Changed from SUPABASE_KEY to match .env
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_JWT_SECRET: Optional[str] = None

    # Neo4j
    NEO4J_URI: str
    NEO4J_USERNAME: str
    NEO4J_PASSWORD: str
    NEO4J_DATABASE: str = "neo4j"
    
    # Redis
    REDIS_URL: Optional[str] = "redis://localhost:6379/0"
    
    # Celery
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None

    # Email
    SENDGRID_API_KEY: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    # Auth
    AUTH_SECRET_KEY: Optional[str] = None
    JWT_ALGORITHM: str = "HS256"

    # Stripe
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    
    # Sentry
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENVIRONMENT: str = "development"
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="ignore"
    )


# Create settings instance
settings = Settings()

# Load CORS settings directly from environment variables
try:
    env_cors_origins = os.getenv("CORS_ORIGINS", '["http://localhost:3000"]')
    env_socketio_cors_origins = os.getenv("SOCKETIO_CORS_ORIGINS", '["http://localhost:3000"]')
    
    # Handle both JSON array format and comma-separated format
    if env_cors_origins.startswith('['):
        import json
        settings.CORS_ORIGINS = json.loads(env_cors_origins)
    else:
        settings.CORS_ORIGINS = [origin.strip() for origin in env_cors_origins.split(",")]
        
    if env_socketio_cors_origins.startswith('['):
        import json
        settings.SOCKETIO_CORS_ORIGINS = json.loads(env_socketio_cors_origins)
    else:
        settings.SOCKETIO_CORS_ORIGINS = [origin.strip() for origin in env_socketio_cors_origins.split(",")]
except Exception as e:
    print(f"Warning: Error parsing CORS settings - {e}")
    # Fallback to default values
    settings.CORS_ORIGINS = ["http://localhost:3000"]
    settings.SOCKETIO_CORS_ORIGINS = ["http://localhost:3000"] 
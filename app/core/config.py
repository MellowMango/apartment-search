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

    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str

    # Neo4j
    NEO4J_URI: str
    NEO4J_USERNAME: str
    NEO4J_PASSWORD: str
    NEO4J_DATABASE: str = "neo4j"

    # Email
    SENDGRID_API_KEY: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None

    # Stripe
    STRIPE_API_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="ignore"
    )


# Create settings instance
settings = Settings()

# Load CORS settings directly from environment variables
env_cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000")
env_socketio_cors_origins = os.getenv("SOCKETIO_CORS_ORIGINS", "http://localhost:3000")

# Add CORS settings as attributes to the settings object
settings.CORS_ORIGINS = [origin.strip() for origin in env_cors_origins.split(",")] if "," in env_cors_origins else [env_cors_origins.strip()]
settings.SOCKETIO_CORS_ORIGINS = [origin.strip() for origin in env_socketio_cors_origins.split(",")] if "," in env_socketio_cors_origins else [env_socketio_cors_origins.strip()] 
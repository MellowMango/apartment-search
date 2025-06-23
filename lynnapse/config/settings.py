"""
Lynnapse application settings.
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    app_name: str = Field(default="Lynnapse", env="APP_NAME")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # MongoDB
    mongodb_url: str = Field(default="mongodb://localhost:27017", env="MONGODB_URL")
    mongodb_database: str = Field(default="lynnapse", env="MONGODB_DATABASE")
    
    # Prefect
    prefect_api_url: Optional[str] = Field(default=None, env="PREFECT_API_URL")
    prefect_api_key: Optional[str] = Field(default=None, env="PREFECT_API_KEY")
    
    # Scraping
    playwright_headless: bool = Field(default=True, env="PLAYWRIGHT_HEADLESS")
    playwright_timeout: int = Field(default=30000, env="PLAYWRIGHT_TIMEOUT")
    max_concurrent_requests: int = Field(default=3, env="MAX_CONCURRENT_REQUESTS")
    request_delay: float = Field(default=1.0, env="REQUEST_DELAY")
    
    # Firecrawl
    firecrawl_api_key: Optional[str] = Field(default=None, env="FIRECRAWL_API_KEY")
    firecrawl_max_retries: int = Field(default=3, env="FIRECRAWL_MAX_RETRIES")
    
    # Retry settings
    max_retries: int = Field(default=3, env="MAX_RETRIES")
    retry_delay: float = Field(default=5.0, env="RETRY_DELAY")
    
    # Output
    output_directory: str = Field(default="./output", env="OUTPUT_DIRECTORY")
    save_raw_html: bool = Field(default=False, env="SAVE_RAW_HTML")
    
    # Logging
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings 
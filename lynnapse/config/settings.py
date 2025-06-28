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
    
    # OpenAI LLM Configuration
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", env="OPENAI_MODEL")
    openai_max_tokens: int = Field(default=1000, env="OPENAI_MAX_TOKENS")
    openai_temperature: float = Field(default=0.1, env="OPENAI_TEMPERATURE")
    openai_timeout: int = Field(default=30, env="OPENAI_TIMEOUT")
    
    # LLM Configuration
    llm_cache_enabled: bool = Field(default=True, env="LLM_CACHE_ENABLED")
    llm_cache_ttl: int = Field(default=86400, env="LLM_CACHE_TTL")  # 24 hours
    llm_max_retries: int = Field(default=3, env="LLM_MAX_RETRIES")
    llm_cost_tracking: bool = Field(default=True, env="LLM_COST_TRACKING")
    
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
        extra = "ignore"  # Ignore extra fields in .env file


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings 
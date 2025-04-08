import os
from typing import Tuple, Type
from pydantic_settings import BaseSettings
import pydantic_settings

print(f"Current working directory: {os.getcwd()}")
print(f"Looking for .env file: minimal.env")

class MinimalSettings(BaseSettings):
    SOCKETIO_CORS_ORIGINS: str

    class Config:
        env_file = 'minimal.env' # Specify the minimal .env file
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
        print("Using custom sources: DotEnv and Init only")
        # Ensure we use the dotenv_settings configured with 'minimal.env'
        return dotenv_settings, init_settings

try:
    print("Attempting to load settings...")
    settings = MinimalSettings()
    print("Settings loaded successfully!")
    print(f"SOCKETIO_CORS_ORIGINS: {settings.SOCKETIO_CORS_ORIGINS}")
    print(f"Type: {type(settings.SOCKETIO_CORS_ORIGINS)}")
except Exception as e:
    print(f"Error loading settings: {e}")
    import traceback
    traceback.print_exc() 
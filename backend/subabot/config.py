from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Build paths inside the project like this: APP_DIR / 'subdir'.
APP_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    subabot_environment: str = Field("development")
    subabot_backend_url: str = Field("http://localhost:8000")
    subabot_frontend_url: str = Field("http://localhost:4321")

    slack_client_id: str = Field(...)
    slack_client_secret: str = Field(...)
    slack_signing_secret: str = Field(...)

    slack_app_id: str = Field(...)
    slack_team_id: str = Field(...)
    slack_channel_id: str = Field(...)


settings = Settings()  # type: ignore

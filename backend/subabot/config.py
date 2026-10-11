from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Old project secrets are never loaded implicitly. Environment variables use a new prefix.
    model_config = SettingsConfigDict(env_prefix="SUBABOT_", extra="ignore")

    database_url: str = "sqlite:///./subabot.db"
    frontend_url: str = "http://localhost:4321"
    trust_proxy_client_ip: bool = False
    proxy_shared_secret: SecretStr = Field(default=SecretStr(""), repr=False)
    scheduler_enabled: bool = True
    scan_interval_seconds: int = Field(default=900, ge=60)
    scan_cooldown_seconds: int = Field(default=15, ge=0)
    feed_timeout_seconds: int = Field(default=12, ge=1, le=60)
    max_feed_bytes: int = Field(default=2_000_000, ge=1000, le=10_000_000)
    max_monitors: int = Field(default=25, ge=1, le=100)

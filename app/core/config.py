"""Settings. The only reader of the environment. Use get_settings()."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEV_SECRET_KEY = "dev-secret-change-me"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SPLITWISE_", env_file=".env", extra="ignore")

    env: Literal["dev", "test", "prod"] = "dev"
    database_path: Path = Path("_data/splitwise.db")
    secret_key: str | None = None
    log_level: str = "INFO"
    log_format: Literal["console", "json"] | None = None
    host: str = "127.0.0.1"
    port: int = 8000

    @model_validator(mode="after")
    def _resolve_defaults(self) -> "Settings":
        if self.secret_key is None:
            if self.env == "prod":
                raise ValueError("SPLITWISE_SECRET_KEY is required when SPLITWISE_ENV is prod")
            self.secret_key = DEV_SECRET_KEY
        if self.log_format is None:
            self.log_format = "console" if self.env == "dev" else "json"
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()

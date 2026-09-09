import os
from typing import Literal
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


def read_secret(secret_file_var: str, default: str = "") -> str:
    path = os.getenv(secret_file_var)
    if path and os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return default


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )

    PROJECT_NAME: str = "Warehouse ERP Engine"
    ENVIRONMENT: Literal["development", "staging", "production"] = "production"
    DEBUG: bool = False

    POSTGRES_SERVER: str = "db"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = read_secret("POSTGRES_PASSWORD_FILE", "postgres")
    POSTGRES_DB: str = "warehouse_erp"

    @computed_field
    @property
    def async_database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    SECRET_KEY: str = read_secret(
        "SECRET_KEY_FILE",
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    AUTO_REPLENISH_ENABLED: bool = True
    AUTO_REPLENISH_INTERVAL_SECONDS: int = 300


settings = Settings()

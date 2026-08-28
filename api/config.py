from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "Hear-Me API"
    VERSION: str = "0.1.0"

    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/hear_me"
    REDIS_URL: str = "redis://localhost:6379/0"

    SECRET_KEY: str = "change-me"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
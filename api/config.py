from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

AppEnv = Literal["development", "production"]

_PLACEHOLDER_KEYS = {"", "change-me", "changeme"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "Hear-Me API"
    VERSION: str = "0.1.0"
    ENV: AppEnv = "development"

    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/hear_me"
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT signing key (HS256). Must be >= 32 bytes. Never reuse for encryption.
    SECRET_KEY: str = "change-me"
    # Fernet key for encrypting stored platform tokens. MUST be separate from
    # SECRET_KEY (never derive one from the other) and >= 32 bytes, else the
    # derived key material is weak.
    TOKEN_ENCRYPTION_KEY: str = "change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    SPOTIFY_CLIENT_ID: str = ""
    SPOTIFY_CLIENT_SECRET: str = ""
    SPOTIFY_REDIRECT_URI: str = "http://localhost:8000/api/auth/spotify/callback"
    SPOTIFY_API_BASE: str = "https://api.spotify.com/v1"
    SPOTIFY_ACCOUNTS_BASE: str = "https://accounts.spotify.com"
    SPOTIFY_MAX_REQUESTS_PER_MINUTE: int = 3000

    MUSICBRAINZ_API_BASE: str = "https://musicbrainz.org/ws/2"
    MUSICBRAINZ_REQUEST_INTERVAL_SECONDS: float = 1.0

    @model_validator(mode="after")
    def validate_production_keys(self) -> "Settings":
        if self.ENV != "production":
            return self
        for name in ("SECRET_KEY", "TOKEN_ENCRYPTION_KEY"):
            value = getattr(self, name)
            if value in _PLACEHOLDER_KEYS or len(value) < 32:
                raise ValueError(
                    f"{name} must be >= 32 bytes and not a placeholder when ENV=production"
                )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
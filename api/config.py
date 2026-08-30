from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "Hear-Me API"
    VERSION: str = "0.1.0"

    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/hear_me"
    REDIS_URL: str = "redis://localhost:6379/0"

    SECRET_KEY: str = "change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    SPOTIFY_CLIENT_ID: str = ""
    SPOTIFY_CLIENT_SECRET: str = ""
    SPOTIFY_REDIRECT_URI: str = "http://localhost:8000/api/auth/spotify/callback"
    SPOTIFY_API_BASE: str = "https://api.spotify.com/v1"
    SPOTIFY_ACCOUNTS_BASE: str = "https://accounts.spotify.com"
    SPOTIFY_MAX_REQUESTS_PER_MINUTE: int = 3000

    MUSICBRAINZ_API_BASE: str = "https://musicbrainz.org/ws/2"
    MUSICBRAINZ_REQUEST_INTERVAL_SECONDS: float = 1.0


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
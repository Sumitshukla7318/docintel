"""
Centralized application configuration.
All settings are loaded from environment variables / .env file.
Never hardcode secrets here — this file only defines shape + defaults.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_NAME: str = "DocIntel"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str
    API_V1_PREFIX: str = "/api/v1"

    # JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # Postgres
    DATABASE_URL: str
    SYNC_DATABASE_URL: str

    # Redis
    REDIS_URL: str
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    # Qdrant
    QDRANT_HOST: str = "qdrant"
    QDRANT_PORT: int = 6333
    QDRANT_URL: str = "http://qdrant:6333"

    # Embeddings
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_DIM: int = 384

    # Gemini
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-3.6-flash"

    # Uploads
    MAX_UPLOAD_SIZE_MB: int = 50
    UPLOAD_DIR: str = "/app/uploads"

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # Chunking defaults
    DEFAULT_CHUNK_SIZE: int = 800
    DEFAULT_CHUNK_OVERLAP: int = 120

    # Retrieval defaults
    DEFAULT_TOP_K: int = 5


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — avoids re-parsing env on every import."""
    return Settings()


settings = get_settings()
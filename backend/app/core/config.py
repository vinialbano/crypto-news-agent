"""Application configuration."""

import os

from pydantic import PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Use .env.test for local testing (set TEST_MODE=1), otherwise use top level .env
        env_file="../.env.test" if os.getenv("TEST_MODE") else "../.env",
        env_ignore_empty=True,
        extra="ignore",
    )

    PROJECT_NAME: str
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost",
        "http://localhost:5173",
        "https://localhost",
        "https://localhost:5173",
    ]

    # Database
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    # Ollama configuration for LLM and embeddings
    OLLAMA_HOST: str
    OLLAMA_CHAT_MODEL: str
    OLLAMA_EMBEDDING_MODEL: str

    # News source RSS URLs
    RSS_DL_NEWS: str
    RSS_THE_DEFIANT: str
    RSS_COINTELEGRAPH: str

    @computed_field  # type: ignore[prop-decorator]
    @property
    def news_sources(self) -> list[dict[str, str]]:
        """Get configured news sources from environment variables."""
        return [
            {"name": "DL News", "rss_url": self.RSS_DL_NEWS},
            {"name": "The Defiant", "rss_url": self.RSS_THE_DEFIANT},
            {"name": "Cointelegraph", "rss_url": self.RSS_COINTELEGRAPH},
        ]

    # Ingestion configuration
    INGESTION_INTERVAL_MINUTES: int
    ARTICLE_CLEANUP_DAYS: int = 30

    # RAG configuration
    RAG_DISTANCE_THRESHOLD: float = 0.5
    RAG_TOP_K_ARTICLES: int = 5
    RAG_CONTEXT_PREVIEW_LENGTH: int = 500

    # WebSocket configuration
    WEBSOCKET_MAX_QUESTIONS_PER_MINUTE: int = 10
    WEBSOCKET_CONNECTION_TIMEOUT_SECONDS: int = 300  # 5 minutes


settings = Settings()  # type: ignore

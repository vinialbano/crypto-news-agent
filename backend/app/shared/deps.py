"""FastAPI dependencies.

This module contains ALL dependency factories for the application.
Following SOLID principles, all external dependencies are injected through this module.

Singleton pattern is used for external service connections (Ollama, etc.) to avoid
creating multiple connections.
"""

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from langchain_ollama import ChatOllama, OllamaEmbeddings
from sqlmodel import Session

from app.core.config import settings
from app.core.db import engine
from app.features.embeddings.service import EmbeddingsService
from app.features.news.article_processor import ArticleProcessor
from app.features.news.ingestion_service import IngestionService
from app.features.news.repository import NewsRepository
from app.features.news.rss_fetcher import RSSFetcher
from app.features.questions.rag_service import RAGService

# ===========================
# Core Dependencies
# ===========================


def get_db() -> Generator[Session, None, None]:
    """Get database session."""
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]


# ===========================
# External Service Singletons (lazy initialized)
# ===========================

_ollama_embeddings: OllamaEmbeddings | None = None
_chat_ollama: ChatOllama | None = None


def get_ollama_embeddings() -> OllamaEmbeddings:
    """Get singleton OllamaEmbeddings instance."""
    global _ollama_embeddings
    if _ollama_embeddings is None:
        _ollama_embeddings = OllamaEmbeddings(
            base_url=settings.OLLAMA_HOST, model=settings.OLLAMA_EMBEDDING_MODEL
        )
    return _ollama_embeddings


def get_chat_ollama() -> ChatOllama:
    """Get singleton ChatOllama instance."""
    global _chat_ollama
    if _chat_ollama is None:
        _chat_ollama = ChatOllama(
            base_url=settings.OLLAMA_HOST,
            model=settings.OLLAMA_CHAT_MODEL,
            temperature=0,  # Deterministic responses
        )
    return _chat_ollama


# ===========================
# Repository Dependencies
# ===========================


def get_news_repository(session: SessionDep) -> NewsRepository:
    """Get news repository instance."""
    return NewsRepository(session)


NewsRepositoryDep = Annotated[NewsRepository, Depends(get_news_repository)]


# ===========================
# Service Dependencies
# ===========================


def get_embeddings_service_dep(
    ollama_embeddings: Annotated[OllamaEmbeddings, Depends(get_ollama_embeddings)],
) -> EmbeddingsService:
    """Get embeddings service dependency."""
    return EmbeddingsService(ollama_embeddings)


def get_rss_fetcher_dep() -> RSSFetcher:
    """Get RSS fetcher dependency."""
    return RSSFetcher()


def get_article_processor_dep(
    embeddings_service: Annotated[EmbeddingsService, Depends(get_embeddings_service_dep)],
    repository: NewsRepositoryDep,
) -> ArticleProcessor:
    """Get article processor dependency."""
    return ArticleProcessor(embeddings_service, repository)


def get_ingestion_service_dep(
    rss_fetcher: Annotated[RSSFetcher, Depends(get_rss_fetcher_dep)],
    article_processor: Annotated[ArticleProcessor, Depends(get_article_processor_dep)],
    repository: NewsRepositoryDep,
) -> IngestionService:
    """Get ingestion service dependency."""
    return IngestionService(rss_fetcher, article_processor, repository)


def get_rag_service_dep(
    embeddings_service: Annotated[EmbeddingsService, Depends(get_embeddings_service_dep)],
    chat_model: Annotated[ChatOllama, Depends(get_chat_ollama)],
    repository: NewsRepositoryDep,
) -> RAGService:
    """Get RAG service dependency."""
    return RAGService(embeddings_service, chat_model, repository)


# ===========================
# Type Annotations for FastAPI
# ===========================

EmbeddingsServiceDep = Annotated[EmbeddingsService, Depends(get_embeddings_service_dep)]
RSSFetcherDep = Annotated[RSSFetcher, Depends(get_rss_fetcher_dep)]
ArticleProcessorDep = Annotated[ArticleProcessor, Depends(get_article_processor_dep)]
IngestionServiceDep = Annotated[IngestionService, Depends(get_ingestion_service_dep)]
RAGServiceDep = Annotated[RAGService, Depends(get_rag_service_dep)]


# ===========================
# Standalone Factories (for scheduled jobs, WebSockets, CLI)
# These use Depends() to automatically resolve dependencies
# ===========================


def create_ingestion_service(
    repository: NewsRepository = Depends(get_news_repository),
    rss_fetcher: RSSFetcher = Depends(get_rss_fetcher_dep),
    article_processor: ArticleProcessor = Depends(get_article_processor_dep),
) -> IngestionService:
    """Create standalone ingestion service for scheduled jobs and CLI."""
    return IngestionService(rss_fetcher, article_processor, repository)


def create_rag_service(
    embeddings_service: EmbeddingsService = Depends(get_embeddings_service_dep),
    chat_model: ChatOllama = Depends(get_chat_ollama),
    repository: NewsRepository = Depends(get_news_repository),
) -> RAGService:
    """Create standalone RAG service for WebSockets and CLI."""
    return RAGService(embeddings_service, chat_model, repository)

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
from app.features.news.article_processor import ArticleProcessor
from app.features.news.ingestion_service import IngestionService
from app.features.news.repository import NewsRepository
from app.features.news.rss_fetcher import RSSFetcher
from app.features.questions.rag_service import RAGService
from app.shared.content_moderation import ContentModerationService
from app.shared.embeddings import EmbeddingsService

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
    session: SessionDep,
) -> IngestionService:
    """Get ingestion service dependency for FastAPI routes."""
    return create_ingestion_service(session)


def get_rag_service_dep(
    embeddings_service: Annotated[EmbeddingsService, Depends(get_embeddings_service_dep)],
    chat_model: Annotated[ChatOllama, Depends(get_chat_ollama)],
    repository: NewsRepositoryDep,
) -> RAGService:
    """Get RAG service dependency."""
    return RAGService(embeddings_service, chat_model, repository)


def get_content_moderation_dep() -> ContentModerationService:
    """Get content moderation service dependency."""
    return ContentModerationService()


# ===========================
# Type Annotations for FastAPI
# ===========================

EmbeddingsServiceDep = Annotated[EmbeddingsService, Depends(get_embeddings_service_dep)]
RSSFetcherDep = Annotated[RSSFetcher, Depends(get_rss_fetcher_dep)]
ArticleProcessorDep = Annotated[ArticleProcessor, Depends(get_article_processor_dep)]
IngestionServiceDep = Annotated[IngestionService, Depends(get_ingestion_service_dep)]
RAGServiceDep = Annotated[RAGService, Depends(get_rag_service_dep)]
ContentModerationDep = Annotated[
    ContentModerationService, Depends(get_content_moderation_dep)
]


# ===========================
# Service Factories (shared construction logic)
# Used by both FastAPI DI and standalone contexts (schedulers, CLI, tests)
# ===========================


def create_ingestion_service(session: Session) -> IngestionService:
    """Create ingestion service with all dependencies.

    This is the core construction logic used by both:
    - FastAPI dependency injection (via get_ingestion_service_dep)
    - Standalone contexts (schedulers, CLI, tests)

    Args:
        session: Database session (managed by caller)

    Returns:
        Fully constructed IngestionService
    """
    embeddings = get_ollama_embeddings()
    embeddings_service = EmbeddingsService(embeddings)
    rss_fetcher = RSSFetcher()
    repository = NewsRepository(session)
    processor = ArticleProcessor(embeddings_service, repository)
    return IngestionService(rss_fetcher, processor, repository)

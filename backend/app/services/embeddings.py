"""Embeddings service using Ollama nomic-embed-text model."""

import logging

from langchain_ollama import OllamaEmbeddings

from app.exceptions import EmbeddingGenerationError

logger = logging.getLogger(__name__)


class EmbeddingsService:
    """Service for generating text embeddings using Ollama."""

    def __init__(self, embeddings: OllamaEmbeddings):
        """Initialize the embeddings service."""
        self._embeddings = embeddings
        logger.info("Initialized EmbeddingsService")

    def embed_query(self, query: str) -> list[float]:
        """Generate embedding for a query string."""
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        try:
            embedding = self._embeddings.embed_query(query)
            logger.debug(f"Generated embedding for query: {query[:50]}...")
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding for query: {e}")
            raise EmbeddingGenerationError(
                f"Failed to generate embedding for query: {e}"
            ) from e

    def embed_documents(self, documents: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple documents."""
        if not documents:
            raise ValueError("Documents list cannot be empty")

        try:
            embeddings = self._embeddings.embed_documents(documents)
            logger.debug(f"Generated embeddings for {len(documents)} documents")
            return embeddings
        except Exception as e:
            logger.error(f"Failed to generate embeddings for documents: {e}")
            raise EmbeddingGenerationError(
                f"Failed to generate embeddings for {len(documents)} documents: {e}"
            ) from e

    async def aembed_query(self, query: str) -> list[float]:
        """Async version of embed_query."""
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        try:
            embedding = await self._embeddings.aembed_query(query)
            logger.debug(f"Generated embedding for query (async): {query[:50]}...")
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding for query (async): {e}")
            raise EmbeddingGenerationError(
                f"Failed to generate embedding for query (async): {e}"
            ) from e

    async def aembed_documents(self, documents: list[str]) -> list[list[float]]:
        """Async version of embed_documents."""
        if not documents:
            raise ValueError("Documents list cannot be empty")

        try:
            embeddings = await self._embeddings.aembed_documents(documents)
            logger.debug(f"Generated embeddings for {len(documents)} documents (async)")
            return embeddings
        except Exception as e:
            logger.error(f"Failed to generate embeddings for documents (async): {e}")
            raise EmbeddingGenerationError(
                f"Failed to generate embeddings for {len(documents)} documents (async): {e}"
            ) from e

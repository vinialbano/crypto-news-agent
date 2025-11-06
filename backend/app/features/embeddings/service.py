"""Embeddings service using Ollama nomic-embed-text model."""
import logging
from typing import Optional

from langchain_ollama import OllamaEmbeddings

logger = logging.getLogger(__name__)


class EmbeddingsService:
    """Service for generating text embeddings using Ollama."""

    def __init__(self, embeddings: OllamaEmbeddings):
        """Initialize the embeddings service with injected embeddings instance.

        Args:
            embeddings: OllamaEmbeddings instance (dependency injection)
        """
        self._embeddings = embeddings
        logger.info("Initialized EmbeddingsService")

    def embed_query(self, query: str) -> list[float]:
        """Generate embedding for a single query string.

        Args:
            query: Text query to embed

        Returns:
            768-dimensional embedding vector

        Raises:
            ValueError: If query is empty
            ConnectionError: If Ollama service is unavailable
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        try:
            embedding = self._embeddings.embed_query(query)
            logger.debug(f"Generated embedding for query: {query[:50]}...")
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding for query: {e}")
            raise

    def embed_documents(self, documents: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple documents.

        Args:
            documents: List of text documents to embed

        Returns:
            List of 768-dimensional embedding vectors

        Raises:
            ValueError: If documents list is empty
            ConnectionError: If Ollama service is unavailable
        """
        if not documents:
            raise ValueError("Documents list cannot be empty")

        try:
            embeddings = self._embeddings.embed_documents(documents)
            logger.debug(f"Generated embeddings for {len(documents)} documents")
            return embeddings
        except Exception as e:
            logger.error(f"Failed to generate embeddings for documents: {e}")
            raise

    async def aembed_query(self, query: str) -> list[float]:
        """Async version of embed_query.

        Args:
            query: Text query to embed

        Returns:
            768-dimensional embedding vector

        Raises:
            ValueError: If query is empty
            ConnectionError: If Ollama service is unavailable
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        try:
            embedding = await self._embeddings.aembed_query(query)
            logger.debug(f"Generated embedding for query (async): {query[:50]}...")
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding for query (async): {e}")
            raise

    async def aembed_documents(self, documents: list[str]) -> list[list[float]]:
        """Async version of embed_documents.

        Args:
            documents: List of text documents to embed

        Returns:
            List of 768-dimensional embedding vectors

        Raises:
            ValueError: If documents list is empty
            ConnectionError: If Ollama service is unavailable
        """
        if not documents:
            raise ValueError("Documents list cannot be empty")

        try:
            embeddings = await self._embeddings.aembed_documents(documents)
            logger.debug(f"Generated embeddings for {len(documents)} documents (async)")
            return embeddings
        except Exception as e:
            logger.error(f"Failed to generate embeddings for documents (async): {e}")
            raise


# Factory function for creating embeddings service
def create_embeddings_service(base_url: str, model: str) -> EmbeddingsService:
    """Create an EmbeddingsService instance.

    Args:
        base_url: Ollama service URL
        model: Embedding model name

    Returns:
        EmbeddingsService instance
    """
    embeddings = OllamaEmbeddings(base_url=base_url, model=model)
    return EmbeddingsService(embeddings)


# Global singleton instance (initialized from config)
_embeddings_service: Optional[EmbeddingsService] = None


def get_embeddings_service() -> EmbeddingsService:
    """Get the global embeddings service instance.

    This is used as a FastAPI dependency.

    Returns:
        EmbeddingsService instance
    """
    global _embeddings_service

    if _embeddings_service is None:
        # Import here to avoid circular dependency
        from app.core.config import settings

        _embeddings_service = create_embeddings_service(
            base_url=settings.OLLAMA_HOST,
            model=settings.OLLAMA_EMBEDDING_MODEL
        )

    return _embeddings_service

"""RAG (Retrieval Augmented Generation) service for question answering."""

import logging
from collections.abc import AsyncIterator

from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from app.core.config import settings
from app.services.news_repository import NewsRepository
from app.services.embeddings import EmbeddingsService
from app.exceptions import InsufficientContextError, RAGError

logger = logging.getLogger(__name__)


class RAGService:
    """Service for question answering using RAG pattern."""

    def __init__(
        self,
        embeddings_service: EmbeddingsService,
        chat_model: ChatOllama,
        repository: NewsRepository,
    ):
        """Initialize RAG service."""
        self.embeddings_service = embeddings_service
        self.chat_model = chat_model
        self.repository = repository

        # Prompt template for RAG
        self.prompt_template = ChatPromptTemplate.from_template(
            """You are a cryptocurrency news assistant. Answer the user's question based on the following news articles.

Context from recent crypto news articles:
{context}

User question: {question}

Instructions:
- Provide a concise, accurate answer based ONLY on the information in the provided articles
- If the articles don't contain enough information, say "I don't have enough information about that topic in recent news"
- Cite specific articles when possible (e.g., "According to DL News...")
- Be objective and factual

Answer:"""
        )

    async def stream_answer(self, question: str) -> AsyncIterator[dict]:
        """Stream an answer to a question using RAG pattern.

        Args:
            question: User's question

        Yields:
            Dictionary with message type and content:
            - {"type": "sources", "count": 3} - Number of source articles used
            - {"type": "chunk", "content": "text..."} - Text chunks
            - {"type": "done"} - Streaming complete
            - {"type": "error", "content": "message"} - Error occurred
        """
        try:
            # Step 1: Generate query embedding
            logger.info(f"Processing question: {question[:100]}")
            query_embedding = await self.embeddings_service.aembed_query(question)

            # Step 2: Semantic search for relevant articles using injected repository
            results = self.repository.semantic_search(
                query_embedding=query_embedding,
                limit=settings.RAG_TOP_K_ARTICLES,
            )

            # Step 3: Check if we have relevant articles
            if not results or results[0][1] > settings.RAG_DISTANCE_THRESHOLD:
                distance = results[0][1] if results else None
                logger.warning(f"No relevant articles found (distance: {distance})")
                raise InsufficientContextError(
                    "No relevant articles found for the given question"
                )

            # Step 4: Build context from retrieved articles
            articles, distances = zip(*results, strict=False)
            context = self._build_context(articles)

            # Send source articles to frontend
            yield {
                "type": "sources",
                "count": len(articles),
                "sources": [
                    {
                        "title": article.title,
                        "source": article.source_name,
                        "url": article.url,
                    }
                    for article in articles
                ],
            }

            logger.info(f"Found {len(articles)} relevant articles, streaming answer")

            # Step 5: Stream LLM response
            formatted_prompt = self.prompt_template.format_messages(
                context=context, question=question
            )

            async for chunk in self.chat_model.astream(formatted_prompt):
                if hasattr(chunk, "content") and chunk.content:
                    yield {"type": "chunk", "content": chunk.content}

            # Step 6: Signal completion
            yield {"type": "done"}

        except InsufficientContextError as e:
            logger.warning(f"Insufficient context: {e}")
            yield {
                "type": "error",
                "content": "I don't have enough information about that topic in recent news.",
            }
        except Exception as e:
            logger.error(f"Error streaming answer: {e}", exc_info=True)
            raise RAGError(f"Failed to generate answer: {e}") from e

    def _build_context(self, articles) -> str:
        """Build context string from retrieved articles."""
        context_parts = []

        for idx, article in enumerate(articles, 1):
            context_parts.append(
                f"Article {idx} (Source: {article.source_name}):\n"
                f"Title: {article.title}\n"
                f"Content: {article.content[:settings.RAG_CONTEXT_PREVIEW_LENGTH]}...\n"
            )

        return "\n\n".join(context_parts)

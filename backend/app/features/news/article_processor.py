"""Article processor for generating embeddings and persisting articles."""

import logging
from datetime import datetime

from app.features.news.models import NewsArticle
from app.features.news.repository import NewsRepository
from app.shared.embeddings import EmbeddingsService

logger = logging.getLogger(__name__)


class ArticleProcessor:
    """Processes articles by generating embeddings and persisting to database."""

    def __init__(
        self, embeddings_service: EmbeddingsService, repository: NewsRepository
    ):
        """Initialize article processor."""
        self.embeddings_service = embeddings_service
        self.repository = repository

    def process_article(
        self,
        title: str,
        url: str,
        content: str,
        source_name: str,
        published_at: datetime | None = None,
    ) -> NewsArticle | None:
        """Process a single article: check for duplicates, generate embedding, and persist.

        Args:
            title: Article title
            url: Article URL
            content: Article content
            source_name: Source name for the article
            published_at: Optional publication date

        Returns:
            Created NewsArticle if successful, None if duplicate or error
        """
        try:
            # Check for duplicates using content hash
            content_hash = NewsArticle.compute_content_hash(title, url)
            existing = self.repository.get_article_by_hash(content_hash)

            if existing:
                logger.debug(f"Duplicate article found: {title}")
                return None

            # Generate embedding from title + content
            embedding_text = f"{title}\n\n{content}"
            embedding = self.embeddings_service.embed_query(embedding_text)

            # Create and persist article
            article = self.repository.create_news_article(
                title=title,
                url=url,
                content=content,
                source_name=source_name,
                published_at=published_at,
                embedding=embedding,
            )

            logger.info(f"Processed article: {title} ({len(content)} chars)")
            return article

        except Exception as e:
            logger.error(f"Error processing article '{title}': {e}")
            raise

    def process_batch(
        self,
        articles: list[dict],
        source_name: str,
    ) -> dict[str, int]:
        """Process a batch of articles and return statistics."""
        stats = {"new_articles": 0, "duplicate_articles": 0, "errors": 0}

        for article_data in articles:
            try:
                result = self.process_article(
                    title=article_data["title"],
                    url=article_data["url"],
                    content=article_data["content"],
                    source_name=source_name,
                    published_at=article_data.get("published_at"),
                )

                if result:
                    stats["new_articles"] += 1
                else:
                    stats["duplicate_articles"] += 1

            except Exception as e:
                logger.error(f"Error in batch processing: {e}")
                stats["errors"] += 1
                continue

        return stats

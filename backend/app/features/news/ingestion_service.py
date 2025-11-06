"""News ingestion service with scheduling support."""

import logging
from datetime import datetime, timedelta

from app.features.news.article_processor import ArticleProcessor
from app.features.news.repository import NewsRepository
from app.features.news.rss_fetcher import RSSFetcher

logger = logging.getLogger(__name__)


class IngestionService:
    """Service for ingesting news articles from RSS feeds.

    Coordinates between RSS fetching and article processing (embeddings + persistence).
    """

    def __init__(
        self,
        rss_fetcher: RSSFetcher,
        article_processor: ArticleProcessor,
        repository: NewsRepository,
    ):
        """Initialize the ingestion service."""
        self.rss_fetcher = rss_fetcher
        self.article_processor = article_processor
        self.repository = repository

    def run_ingestion(self) -> dict:
        """Run news ingestion for all active sources.

        Fetches articles from RSS feeds and processes them (generates embeddings + persists).

        Returns:
            Dictionary with ingestion statistics
        """
        logger.info("Starting news ingestion")
        start_time = datetime.utcnow()

        # Get all active sources
        sources = self.repository.get_active_news_sources()

        if not sources:
            logger.warning("No active news sources found")
            return {
                "sources_processed": 0,
                "total_new_articles": 0,
                "total_duplicates": 0,
                "total_errors": 0,
                "duration_seconds": 0,
            }

        logger.info(f"Processing {len(sources)} active news sources")

        total_stats = {
            "sources_processed": len(sources),
            "total_new_articles": 0,
            "total_duplicates": 0,
            "total_errors": 0,
        }

        # Process each source
        for source in sources:
            # Store source info to avoid lazy-loading issues after rollback
            source_name = source.name
            source_id = source.id

            try:
                # Step 1: Fetch and parse articles from RSS feed
                articles = self.rss_fetcher.fetch_feed(source)

                if not articles:
                    logger.warning(f"No articles fetched from {source_name}")
                    # Update source ingestion status
                    self.repository.update_ingestion_status(
                        source_id=source_id,
                        success=True,
                        error_message=None,
                    )
                    continue

                # Step 2: Process articles (check duplicates, generate embeddings, persist)
                processing_stats = self.article_processor.process_batch(
                    articles=articles,
                    source_name=source_name,
                )

                # Aggregate statistics
                total_stats["total_new_articles"] += processing_stats["new_articles"]
                total_stats["total_duplicates"] += processing_stats[
                    "duplicate_articles"
                ]
                total_stats["total_errors"] += processing_stats["errors"]

                # Update source ingestion status
                self.repository.update_ingestion_status(
                    source_id=source_id,
                    success=True,
                    error_message=None,
                )

                logger.info(
                    f"Completed {source_name}: "
                    f"{processing_stats['new_articles']} new, "
                    f"{processing_stats['duplicate_articles']} duplicates, "
                    f"{processing_stats['errors']} errors"
                )

            except Exception as e:
                error_msg = f"Failed to ingest from source: {e}"
                logger.error(f"{source_name}: {error_msg}", exc_info=True)
                total_stats["total_errors"] += 1

                # Rollback session on error
                self.repository.session.rollback()

                # Update source with error
                self.repository.update_ingestion_status(
                    source_id=source_id,
                    success=False,
                    error_message=error_msg,
                )

        duration = (datetime.utcnow() - start_time).total_seconds()
        total_stats["duration_seconds"] = duration

        logger.info(
            f"Ingestion completed in {duration:.2f}s: "
            f"{total_stats['sources_processed']} sources, "
            f"{total_stats['total_new_articles']} new articles, "
            f"{total_stats['total_duplicates']} duplicates, "
            f"{total_stats['total_errors']} errors"
        )

        return total_stats

    def cleanup_old_articles(self, days: int = 30) -> int:
        """Delete articles older than specified days."""
        logger.info(f"Cleaning up articles older than {days} days")
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        deleted_count = self.repository.delete_old_articles(cutoff_date)

        logger.info(f"Deleted {deleted_count} old articles")
        return deleted_count

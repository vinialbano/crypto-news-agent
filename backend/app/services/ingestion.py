"""News ingestion service with scheduling support."""

import logging
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.exceptions import RSSFetchError
from app.services.article_processor import ArticleProcessor
from app.services.news_repository import NewsRepository
from app.services.rss_fetcher import RSSFetcher

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

    def ingest_source(self, source_name: str) -> dict:
        """Ingest articles from a single news source.

        Args:
            source_name: Name of the news source to ingest

        Returns:
            Dictionary with detailed ingestion statistics: {
                "source_name": str,
                "new_articles": int,
                "duplicates": int,
                "errors": int,
                "duration_seconds": float,
                "success": bool,
                "error_message": str | None,
            }

        Raises:
            ValueError: If source name is not found in configuration
        """
        # Get source from configuration
        source = self.repository.get_source_by_name(source_name)
        if source is None:
            raise ValueError(f"Source '{source_name}' not found in configuration")

        logger.info(f"Starting ingestion for source: {source_name}")
        start_time = datetime.now(timezone.utc)

        result = {
            "source_name": source_name,
            "new_articles": 0,
            "duplicates": 0,
            "errors": 0,
            "duration_seconds": 0.0,
            "success": False,
            "error_message": None,
        }

        try:
            # Step 1: Fetch and parse articles from RSS feed
            articles = self.rss_fetcher.fetch_feed(source)

            if not articles:
                logger.warning(f"No articles fetched from {source_name}")
                result["success"] = True
                result["duration_seconds"] = (
                    datetime.now(timezone.utc) - start_time
                ).total_seconds()
                logger.info(f"Completed {source_name}: No new articles")
                return result

            # Step 2: Process articles (check duplicates, generate embeddings, persist)
            processing_stats = self.article_processor.process_batch(
                articles=articles,
                source_name=source_name,
            )

            # Update result with processing stats
            result["new_articles"] = processing_stats["new_articles"]
            result["duplicates"] = processing_stats["duplicate_articles"]
            result["errors"] = processing_stats["errors"]

            result["success"] = True
            logger.info(
                f"Completed {source_name}: "
                f"{result['new_articles']} new, "
                f"{result['duplicates']} duplicates, "
                f"{result['errors']} errors"
            )

        except RSSFetchError as e:
            error_msg = f"RSS fetch failed: {e}"
            logger.error(f"{source_name}: {error_msg}", exc_info=True)
            result["errors"] += 1
            result["error_message"] = error_msg

        except Exception as e:
            error_msg = f"Unexpected error during ingestion: {e}"
            logger.error(f"{source_name}: {error_msg}", exc_info=True)
            result["errors"] += 1
            result["error_message"] = error_msg

        result["duration_seconds"] = (datetime.now(timezone.utc) - start_time).total_seconds()
        return result

    def ingest_all_sources(self) -> dict:
        """Ingest articles from all active sources sequentially.

        Returns:
            Dictionary with aggregate statistics: {
                "sources_processed": int,
                "sources_succeeded": int,
                "sources_failed": int,
                "total_new_articles": int,
                "total_duplicates": int,
                "total_errors": int,
                "duration_seconds": float,
                "source_results": list[dict],
            }
        """
        logger.info("Starting news ingestion for all active sources")
        start_time = datetime.now(timezone.utc)

        # Get all active sources
        sources = self.repository.get_active_news_sources()

        if not sources:
            logger.warning("No active news sources found")
            return {
                "sources_processed": 0,
                "sources_succeeded": 0,
                "sources_failed": 0,
                "total_new_articles": 0,
                "total_duplicates": 0,
                "total_errors": 0,
                "duration_seconds": 0.0,
                "source_results": [],
            }

        logger.info(f"Processing {len(sources)} active news sources")

        source_results = []
        total_stats = {
            "sources_processed": len(sources),
            "sources_succeeded": 0,
            "sources_failed": 0,
            "total_new_articles": 0,
            "total_duplicates": 0,
            "total_errors": 0,
        }

        # Process each source
        for source in sources:
            source_name = source["name"]
            result = self.ingest_source(source_name)
            source_results.append(result)

            # Aggregate statistics
            total_stats["total_new_articles"] += result["new_articles"]
            total_stats["total_duplicates"] += result["duplicates"]
            total_stats["total_errors"] += result["errors"]

            if result["success"]:
                total_stats["sources_succeeded"] += 1
            else:
                total_stats["sources_failed"] += 1

        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        total_stats["duration_seconds"] = duration
        total_stats["source_results"] = source_results

        logger.info(
            f"Ingestion completed in {duration:.2f}s: "
            f"{total_stats['sources_processed']} sources "
            f"({total_stats['sources_succeeded']} succeeded, {total_stats['sources_failed']} failed), "
            f"{total_stats['total_new_articles']} new articles, "
            f"{total_stats['total_duplicates']} duplicates, "
            f"{total_stats['total_errors']} errors"
        )

        return total_stats

    def cleanup_old_articles(self, days: int | None = None) -> int:
        """Delete articles older than specified days."""
        if days is None:
            days = settings.ARTICLE_CLEANUP_DAYS

        logger.info(f"Cleaning up articles older than {days} days")
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        deleted_count = self.repository.delete_old_articles(cutoff_date)

        logger.info(f"Deleted {deleted_count} old articles")
        return deleted_count

"""Unit tests for ingestion service."""

from unittest.mock import MagicMock

import pytest

from app.services.ingestion import IngestionService


@pytest.fixture
def mock_rss_fetcher():
    return MagicMock()


@pytest.fixture
def mock_article_processor():
    return MagicMock()


@pytest.fixture
def mock_repository():
    return MagicMock()


@pytest.fixture
def ingestion_service(mock_rss_fetcher, mock_article_processor, mock_repository):
    return IngestionService(
        rss_fetcher=mock_rss_fetcher,
        article_processor=mock_article_processor,
        repository=mock_repository,
    )


class TestIngestionService:
    def test_ingest_source_success(
        self,
        ingestion_service,
        mock_rss_fetcher,
        mock_article_processor,
        mock_repository,
    ):
        """Test ingesting a single source by passing source name."""
        mock_source = {
            "name": "Test Source",
            "rss_url": "https://example.com/rss",
        }
        mock_repository.get_source_by_name.return_value = mock_source

        mock_rss_fetcher.fetch_feed.return_value = [
            {
                "title": "Article 1",
                "url": "http://example.com/1",
                "content": "Content 1",
                "published_at": None,
            }
        ]

        mock_article_processor.process_batch.return_value = {
            "new_articles": 1,
            "duplicate_articles": 0,
            "errors": 0,
        }

        result = ingestion_service.ingest_source("Test Source")

        assert result["source_name"] == "Test Source"
        assert result["new_articles"] == 1
        assert result["duplicates"] == 0
        assert result["errors"] == 0
        assert result["success"] is True
        assert result["error_message"] is None
        assert "duration_seconds" in result
        mock_repository.get_source_by_name.assert_called_once_with("Test Source")
        mock_rss_fetcher.fetch_feed.assert_called_once_with(mock_source)
        mock_article_processor.process_batch.assert_called_once()

    def test_ingest_source_not_found(self, ingestion_service, mock_repository):
        """Test ingesting with invalid source name raises ValueError."""
        mock_repository.get_source_by_name.return_value = None

        with pytest.raises(ValueError, match="Source 'Unknown Source' not found"):
            ingestion_service.ingest_source("Unknown Source")

    def test_ingest_source_with_errors(
        self,
        ingestion_service,
        mock_rss_fetcher,
        mock_article_processor,
        mock_repository,
    ):
        """Test ingesting source with processing errors."""
        mock_source = {
            "name": "Test Source",
            "rss_url": "https://example.com/rss",
        }
        mock_repository.get_source_by_name.return_value = mock_source

        mock_rss_fetcher.fetch_feed.return_value = [
            {
                "title": "Article 1",
                "url": "http://example.com/1",
                "content": "Content 1",
                "published_at": None,
            }
        ]

        mock_article_processor.process_batch.return_value = {
            "new_articles": 20,
            "duplicate_articles": 5,
            "errors": 2,
        }

        result = ingestion_service.ingest_source("Test Source")

        assert result["errors"] == 2
        assert result["new_articles"] == 20
        assert result["duplicates"] == 5
        assert result["success"] is True  # Still success despite processing errors

    def test_ingest_source_exception_handling(
        self, ingestion_service, mock_rss_fetcher, mock_repository
    ):
        """Test exception handling during source ingestion."""
        mock_source = {
            "name": "Test Source",
            "rss_url": "https://example.com/rss",
        }
        mock_repository.get_source_by_name.return_value = mock_source

        mock_rss_fetcher.fetch_feed.side_effect = Exception("Network error")

        result = ingestion_service.ingest_source("Test Source")

        assert result["success"] is False
        assert result["errors"] >= 1
        assert "Network error" in result["error_message"]

    def test_ingest_all_sources_success(
        self,
        ingestion_service,
        mock_rss_fetcher,
        mock_article_processor,
        mock_repository,
    ):
        """Test ingesting all active sources."""
        mock_source1 = {
            "name": "Source 1",
            "rss_url": "https://example.com/rss1",
        }
        mock_source2 = {
            "name": "Source 2",
            "rss_url": "https://example.com/rss2",
        }
        mock_repository.get_active_news_sources.return_value = [
            mock_source1,
            mock_source2,
        ]

        # Mock get_source_by_name for individual source lookups
        def get_source_by_name(name):
            if name == "Source 1":
                return mock_source1
            elif name == "Source 2":
                return mock_source2
            return None
        mock_repository.get_source_by_name.side_effect = get_source_by_name

        mock_rss_fetcher.fetch_feed.return_value = [
            {
                "title": "Article 1",
                "url": "http://example.com/1",
                "content": "Content 1",
                "published_at": None,
            }
        ]

        mock_article_processor.process_batch.return_value = {
            "new_articles": 1,
            "duplicate_articles": 0,
            "errors": 0,
        }

        result = ingestion_service.ingest_all_sources()

        assert result["sources_processed"] == 2
        assert result["sources_succeeded"] == 2
        assert result["sources_failed"] == 0
        assert result["total_new_articles"] == 2
        assert result["total_duplicates"] == 0
        assert result["total_errors"] == 0
        assert "duration_seconds" in result
        assert len(result["source_results"]) == 2
        assert mock_rss_fetcher.fetch_feed.call_count == 2

    def test_ingest_all_sources_no_sources(self, ingestion_service, mock_repository):
        """Test ingesting when no sources are active."""
        mock_repository.get_active_news_sources.return_value = []

        result = ingestion_service.ingest_all_sources()

        assert result["sources_processed"] == 0
        assert result["sources_succeeded"] == 0
        assert result["sources_failed"] == 0
        assert result["total_new_articles"] == 0
        assert result["total_duplicates"] == 0
        assert result["total_errors"] == 0

    def test_cleanup_old_articles(self, ingestion_service, mock_repository):
        mock_repository.delete_old_articles.return_value = 15

        deleted_count = ingestion_service.cleanup_old_articles(days=30)

        assert deleted_count == 15
        mock_repository.delete_old_articles.assert_called_once()

    def test_cleanup_old_articles_default_days(
        self, ingestion_service, mock_repository
    ):
        mock_repository.delete_old_articles.return_value = 5

        deleted_count = ingestion_service.cleanup_old_articles()

        assert deleted_count == 5
        mock_repository.delete_old_articles.assert_called_once()

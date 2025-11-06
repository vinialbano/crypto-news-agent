"""Unit tests for ingestion service."""

from unittest.mock import MagicMock

import pytest

from app.features.news.ingestion_service import IngestionService
from app.features.news.models import NewsSource


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
    def test_run_ingestion_success(
        self,
        ingestion_service,
        mock_rss_fetcher,
        mock_article_processor,
        mock_repository,
    ):
        mock_source = NewsSource(
            id=1, name="Test Source", rss_url="https://example.com/rss", is_active=True
        )
        mock_repository.get_active_news_sources.return_value = [mock_source]

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

        result = ingestion_service.run_ingestion()

        assert result["sources_processed"] == 1
        assert result["total_new_articles"] == 1
        assert result["total_duplicates"] == 0
        assert result["total_errors"] == 0
        assert "duration_seconds" in result
        mock_rss_fetcher.fetch_feed.assert_called_once_with(mock_source)
        mock_article_processor.process_batch.assert_called_once()

    def test_run_ingestion_with_errors(
        self,
        ingestion_service,
        mock_rss_fetcher,
        mock_article_processor,
        mock_repository,
    ):
        mock_source = NewsSource(
            id=1, name="Test Source", rss_url="https://example.com/rss", is_active=True
        )
        mock_repository.get_active_news_sources.return_value = [mock_source]

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

        result = ingestion_service.run_ingestion()

        assert result["total_errors"] == 2
        assert result["total_new_articles"] == 20

    def test_run_ingestion_exception_handling(
        self, ingestion_service, mock_rss_fetcher, mock_repository
    ):
        mock_source = NewsSource(
            id=1, name="Test Source", rss_url="https://example.com/rss", is_active=True
        )
        mock_repository.get_active_news_sources.return_value = [mock_source]

        mock_rss_fetcher.fetch_feed.side_effect = Exception("Network error")

        result = ingestion_service.run_ingestion()

        assert result["total_errors"] == 1
        assert result["sources_processed"] == 1
        assert mock_repository.update_ingestion_status.call_count == 1

    def test_run_ingestion_no_sources(self, ingestion_service, mock_repository):
        mock_repository.get_active_news_sources.return_value = []

        result = ingestion_service.run_ingestion()

        assert result["sources_processed"] == 0
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

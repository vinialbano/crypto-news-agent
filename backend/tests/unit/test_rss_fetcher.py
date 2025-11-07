"""Unit tests for RSS fetcher with LangChain RSSFeedLoader."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.documents import Document

from app.models import NewsSource
from app.services.rss_fetcher import RSSFetcher


@pytest.fixture
def rss_fetcher():
    return RSSFetcher()


@pytest.fixture
def mock_news_source():
    return NewsSource(
        id=1,
        name="Test News",
        rss_url="https://example.com/rss",
        is_active=True,
    )


class TestRSSFetcher:
    def test_parse_published_date_valid_iso(self, rss_fetcher):
        metadata = {"publish_date": "2025-01-15T10:30:00Z"}
        result = rss_fetcher._parse_published_date(metadata)

        assert result is not None
        assert isinstance(result, datetime)
        assert result.year == 2025
        assert result.month == 1
        assert result.day == 15

    def test_parse_published_date_missing(self, rss_fetcher):
        metadata = {}
        result = rss_fetcher._parse_published_date(metadata)

        assert result is None

    def test_parse_published_date_invalid(self, rss_fetcher):
        metadata = {"publish_date": "not-a-date"}
        result = rss_fetcher._parse_published_date(metadata)

        assert result is None

    @patch("app.services.rss_fetcher.RSSFeedLoader")
    def test_fetch_feed_success(self, mock_loader_class, rss_fetcher, mock_news_source):
        mock_docs = [
            Document(
                page_content="This is a test article about Bitcoin with more than one hundred characters to ensure it passes the validation check properly without any issues.",
                metadata={
                    "title": "Bitcoin News",
                    "link": "https://example.com/article1",
                    "publish_date": "2025-01-15T10:00:00Z",
                },
            ),
            Document(
                page_content="Another test article about Ethereum with sufficient length for content validation requirements and more text to exceed minimum.",
                metadata={
                    "title": "Ethereum Update",
                    "link": "https://example.com/article2",
                    "publish_date": "2025-01-15T11:00:00Z",
                },
            ),
        ]

        mock_loader = MagicMock()
        mock_loader.load.return_value = mock_docs
        mock_loader_class.return_value = mock_loader

        articles = rss_fetcher.fetch_feed(mock_news_source)

        assert len(articles) == 2
        assert articles[0]["title"] == "Bitcoin News"
        assert articles[0]["url"] == "https://example.com/article1"
        assert len(articles[0]["content"]) > 100
        assert articles[1]["title"] == "Ethereum Update"
        assert articles[1]["url"] == "https://example.com/article2"

        mock_loader_class.assert_called_once_with(
            urls=[mock_news_source.rss_url],
            continue_on_failure=True,
            nlp=False,
        )

    @patch("app.services.rss_fetcher.RSSFeedLoader")
    def test_fetch_feed_short_content_skipped(
        self, mock_loader_class, rss_fetcher, mock_news_source
    ):
        mock_docs = [
            Document(
                page_content="Too short",
                metadata={
                    "title": "Short Article",
                    "link": "https://example.com/article1",
                },
            ),
        ]

        mock_loader = MagicMock()
        mock_loader.load.return_value = mock_docs
        mock_loader_class.return_value = mock_loader

        articles = rss_fetcher.fetch_feed(mock_news_source)

        assert len(articles) == 0

    @patch("app.services.rss_fetcher.RSSFeedLoader")
    def test_fetch_feed_missing_metadata(
        self, mock_loader_class, rss_fetcher, mock_news_source
    ):
        mock_docs = [
            Document(
                page_content="Valid content that is long enough to pass validation checks and contains more than one hundred characters of text.",
                metadata={
                    "title": "",
                    "link": "https://example.com/article1",
                },
            ),
            Document(
                page_content="Another valid content that meets the minimum length requirement and has sufficient text to exceed one hundred characters.",
                metadata={
                    "title": "Valid Title",
                    "link": "",
                },
            ),
        ]

        mock_loader = MagicMock()
        mock_loader.load.return_value = mock_docs
        mock_loader_class.return_value = mock_loader

        articles = rss_fetcher.fetch_feed(mock_news_source)

        assert len(articles) == 0

    @patch("app.services.rss_fetcher.RSSFeedLoader")
    def test_fetch_feed_loader_exception(
        self, mock_loader_class, rss_fetcher, mock_news_source
    ):
        import pytest
        from app.exceptions import RSSFetchError

        mock_loader = MagicMock()
        mock_loader.load.side_effect = Exception("Network error")
        mock_loader_class.return_value = mock_loader

        with pytest.raises(RSSFetchError, match="Failed to fetch RSS feed"):
            rss_fetcher.fetch_feed(mock_news_source)

    @patch("app.services.rss_fetcher.RSSFeedLoader")
    def test_fetch_feed_empty_results(
        self, mock_loader_class, rss_fetcher, mock_news_source
    ):
        mock_loader = MagicMock()
        mock_loader.load.return_value = []
        mock_loader_class.return_value = mock_loader

        articles = rss_fetcher.fetch_feed(mock_news_source)

        assert len(articles) == 0

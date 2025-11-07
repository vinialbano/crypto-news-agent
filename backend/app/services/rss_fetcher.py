"""RSS feed fetcher for news ingestion using LangChain RSSFeedLoader."""

import logging
from datetime import datetime
from typing import Any

from langchain_community.document_loaders import RSSFeedLoader

from app.models import NewsSource
from app.exceptions import RSSFetchError

logger = logging.getLogger(__name__)


class RSSFetcher:
    """Fetches and parses RSS feeds into structured article data."""

    def __init__(self):
        """Initialize RSS fetcher."""
        pass

    def _parse_published_date(self, metadata: dict) -> datetime | None:
        """Parse published date from document metadata."""
        # RSSFeedLoader stores publish_date in metadata
        published = metadata.get("publish_date")
        if published:
            try:
                # RSSFeedLoader may return datetime objects or strings
                if isinstance(published, datetime):
                    return published
                # Try to parse string datetime
                from dateutil import parser

                return parser.parse(published)
            except Exception as e:
                logger.warning(f"Failed to parse publish_date '{published}': {e}")

        return None

    def fetch_feed(self, source: NewsSource) -> list[dict[str, Any]]:
        """Fetch and parse a single RSS feed using LangChain RSSFeedLoader.

        Args:
            source: News source to fetch

        Returns:
            List of article dictionaries with 'title', 'url', 'content', and 'published_at' keys
            Returns empty list if fetch fails
        """
        articles = []

        try:
            logger.info(f"Fetching RSS feed from {source.name}: {source.rss_url}")

            # Use LangChain RSSFeedLoader to fetch and parse articles
            # This will automatically extract full article content using newspaper3k
            loader = RSSFeedLoader(
                urls=[source.rss_url],
                continue_on_failure=True,  # Don't crash on individual article failures
                nlp=False,  # Disabled for stability - some sources (Twitter, etc.) cause errors
            )

            # Load documents (each document is a full article)
            documents = loader.load()

            if not documents:
                logger.warning(f"No articles loaded from {source.name}")
                return articles

            logger.info(f"Loaded {len(documents)} articles from {source.name}")

            # Process each document
            for doc in documents:
                try:
                    # Extract metadata
                    title = doc.metadata.get("title", "").strip()
                    url = doc.metadata.get("link", "").strip()
                    content = doc.page_content.strip()

                    if not title or not url:
                        logger.warning("Skipping document with missing title or URL")
                        continue

                    # Skip if content is too short (likely extraction failed)
                    if len(content) < 100:
                        logger.warning(
                            f"Skipping article '{title}' - content too short ({len(content)} chars)"
                        )
                        continue

                    # Parse published date
                    published_at = self._parse_published_date(doc.metadata)

                    # Add parsed article to list
                    articles.append(
                        {
                            "title": title,
                            "url": url,
                            "content": content,
                            "published_at": published_at,
                        }
                    )

                    logger.debug(f"Parsed article: {title} ({len(content)} chars)")

                except Exception as e:
                    logger.error(f"Error parsing document from {source.name}: {e}")
                    continue

            logger.info(
                f"Completed parsing {source.name}: {len(articles)} articles extracted"
            )

        except Exception as e:
            logger.error(
                f"Failed to fetch/parse RSS feed from {source.name}: {e}", exc_info=True
            )
            raise RSSFetchError(
                f"Failed to fetch RSS feed from {source.name}: {e}"
            ) from e

        return articles

"""Seed and update database with configured news sources."""

import logging

from sqlmodel import Session, select

from app.core.config import settings
from app.core.db import engine
from app.models import NewsSource

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_news_sources(session: Session | None = None) -> None:
    """Seed/update the database with news sources from configuration.

    Creates new sources or updates existing ones if RSS URL has changed.

    Args:
        session: Optional database session. If not provided, creates a new one.
    """
    sources_config = [
        {
            "name": "DL News",
            "rss_url": settings.RSS_DL_NEWS,
        },
        {
            "name": "The Defiant",
            "rss_url": settings.RSS_THE_DEFIANT,
        },
        {
            "name": "Cointelegraph",
            "rss_url": settings.RSS_COINTELEGRAPH,
        },
    ]

    # Use provided session or create a new one
    should_manage_session = session is None
    if should_manage_session:
        session = Session(engine)

    try:
        for source_config in sources_config:
            # Check if source exists
            statement = select(NewsSource).where(
                NewsSource.name == source_config["name"]
            )
            existing_source = session.exec(statement).first()

            if existing_source:
                # Update RSS URL if it has changed
                if existing_source.rss_url != source_config["rss_url"]:
                    logger.info(
                        f"Updating RSS URL for '{source_config['name']}' from "
                        f"{existing_source.rss_url} to {source_config['rss_url']}"
                    )
                    existing_source.rss_url = source_config["rss_url"]
                    session.add(existing_source)
                    if should_manage_session:
                        session.commit()
                else:
                    logger.info(f"News source '{source_config['name']}' is up to date")
                continue

            # Create new source
            try:
                source = NewsSource(
                    name=source_config["name"],
                    rss_url=source_config["rss_url"],
                    is_active=True,
                )
                session.add(source)
                if should_manage_session:
                    session.commit()
                logger.info(f"Created news source: {source.name}")
            except Exception as e:
                logger.error(f"Failed to create source '{source_config['name']}': {e}")
                if should_manage_session:
                    session.rollback()
                continue

        logger.info("✓ News sources seeding/update complete")
    finally:
        # Only close session if we created it
        if should_manage_session:
            session.close()


if __name__ == "__main__":
    logger.info("Starting news sources seeding...")
    seed_news_sources()

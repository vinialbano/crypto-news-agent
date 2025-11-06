"""Background job scheduler using APScheduler."""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = AsyncIOScheduler()


# ===========================
# Scheduled Job Functions
# ===========================


def run_scheduled_ingestion() -> None:
    """Run news ingestion as a scheduled job."""
    try:
        from app.shared.deps import create_ingestion_service, get_db

        # Use dependency injection via the factory
        db_gen = get_db()
        session = next(db_gen)
        try:
            service = create_ingestion_service()
            service.run_ingestion()
        finally:
            try:
                db_gen.close()
            except StopIteration:
                pass
    except Exception as e:
        logger.error(f"Scheduled ingestion failed: {e}", exc_info=True)


def run_scheduled_cleanup(days: int = 30) -> None:
    """Run article cleanup as a scheduled job."""
    try:
        from app.shared.deps import create_ingestion_service, get_db

        # Use dependency injection via the factory
        db_gen = get_db()
        session = next(db_gen)
        try:
            service = create_ingestion_service()
            service.cleanup_old_articles(days=days)
        finally:
            try:
                db_gen.close()
            except StopIteration:
                pass
    except Exception as e:
        logger.error(f"Scheduled cleanup failed: {e}", exc_info=True)


# ===========================
# Job Registration
# ===========================


def schedule_news_ingestion() -> None:
    """Schedule periodic news ingestion job."""
    # Run every N minutes (configured in settings)
    interval_minutes = getattr(settings, "INGESTION_INTERVAL_MINUTES", 30)

    scheduler.add_job(
        run_scheduled_ingestion,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id="news_ingestion",
        name="News Ingestion",
        replace_existing=True,
        max_instances=1,  # Don't run multiple ingestion jobs simultaneously
    )

    logger.info(f"Scheduled news ingestion every {interval_minutes} minutes")


def schedule_article_cleanup() -> None:
    """Schedule daily article cleanup job."""
    # Run daily at 2 AM UTC
    scheduler.add_job(
        lambda: run_scheduled_cleanup(days=30),
        trigger=CronTrigger(hour=2, minute=0),
        id="article_cleanup",
        name="Article Cleanup",
        replace_existing=True,
    )

    logger.info("Scheduled article cleanup daily at 2 AM UTC")


def start_scheduler() -> None:
    """Start the scheduler and register all jobs."""
    if scheduler.running:
        logger.warning("Scheduler is already running")
        return

    logger.info("Starting background job scheduler")

    # Register all scheduled jobs
    schedule_news_ingestion()
    schedule_article_cleanup()

    # Start the scheduler
    scheduler.start()
    logger.info("Scheduler started successfully")


def stop_scheduler() -> None:
    """Stop the scheduler."""
    if not scheduler.running:
        logger.warning("Scheduler is not running")
        return

    logger.info("Stopping background job scheduler")
    scheduler.shutdown(wait=True)
    logger.info("Scheduler stopped")

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.jobs import refresh_quotes, recalculate_aggregates

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def start_scheduler() -> None:
    """Start the background scheduler with configured jobs."""
    if scheduler.running:
        logger.warning("Scheduler is already running")
        return

    try:
        # Refresh stock quotes every 5 minutes
        scheduler.add_job(
            refresh_quotes,
            trigger=IntervalTrigger(minutes=5),
            id="refresh_quotes",
            name="Refresh Stock Quotes",
            replace_existing=True,
        )

        # Recalculate portfolio aggregates every 15 minutes
        scheduler.add_job(
            recalculate_aggregates,
            trigger=IntervalTrigger(minutes=15),
            id="recalculate_aggregates",
            name="Recalculate Portfolio Aggregates",
            replace_existing=True,
        )

        scheduler.start()
        logger.info("Background scheduler started successfully")

    except Exception as e:
        logger.error(f"Failed to start scheduler: {str(e)}")
        raise


def stop_scheduler() -> None:
    """Stop the background scheduler."""
    if not scheduler.running:
        logger.debug("Scheduler is not running")
        return

    try:
        scheduler.shutdown(wait=False)
        logger.info("Background scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {str(e)}")

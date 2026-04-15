import logging
from zoneinfo import ZoneInfo

from apscheduler.schedulers.blocking import BlockingScheduler

from app.config import settings
from app.database import SessionLocal
from app.services.digest import run_digest


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
LOGGER = logging.getLogger(__name__)


def scheduled_digest() -> None:
    db = SessionLocal()
    try:
        run_digest(db)
    finally:
        db.close()


def main() -> None:
    scheduler = BlockingScheduler(timezone=ZoneInfo(settings.timezone))
    scheduler.add_job(scheduled_digest, "cron", hour=8, minute=0, id="daily_digest")
    LOGGER.info("Scheduler started for 08:00 %s", settings.timezone)
    scheduler.start()


if __name__ == "__main__":
    main()

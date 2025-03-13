from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "austin_multifamily_map",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Chicago",
    enable_utc=True,
)

# Configure periodic tasks
celery_app.conf.beat_schedule = {
    "scrape-broker-websites-daily": {
        "task": "app.workers.tasks.scraping.scrape_broker_websites",
        "schedule": crontab(hour=1, minute=0),  # Run at 1:00 AM every day
    },
    "check-emails-hourly": {
        "task": "app.workers.tasks.email_processing.check_emails",
        "schedule": crontab(minute=0),  # Run every hour
    },
    "sync-neo4j-daily": {
        "task": "app.workers.tasks.neo4j_sync.sync_neo4j",
        "schedule": crontab(hour=2, minute=0),  # Run at 2:00 AM every day
    },
    "check-missing-info-weekly": {
        "task": "app.workers.tasks.missing_info.check_missing_info",
        "schedule": crontab(day_of_week=1, hour=9, minute=0),  # Run at 9:00 AM every Monday
    },
}

# Import tasks to ensure they are registered
import app.workers.tasks 
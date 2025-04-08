from celery import Celery
from celery.schedules import crontab

# Relative imports
from ..core.config import settings

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
# Use relative paths for tasks within the app structure
celery_app.conf.beat_schedule = {
    "scrape-broker-websites-daily": {
        "task": "backend.app.workers.tasks.scraping.scrape_broker_websites", # Adjusted path
        "schedule": crontab(hour=1, minute=0),  # Run at 1:00 AM every day
    },
    "check-emails-hourly": {
        "task": "backend.app.workers.tasks.email_processing.check_emails", # Adjusted path
        "schedule": crontab(minute=0),  # Run every hour
    },
    "sync-neo4j-daily": {
        "task": "backend.app.workers.tasks.neo4j_sync.sync_neo4j", # Adjusted path
        "schedule": crontab(hour=2, minute=0),  # Run at 2:00 AM every day
    },
    "check-missing-info-weekly": {
        "task": "backend.app.workers.tasks.missing_info.check_missing_info", # Adjusted path
        "schedule": crontab(day_of_week=1, hour=9, minute=0),  # Run at 9:00 AM every Monday
    },
}

# Import tasks using relative paths if possible, or adjust based on execution context
# This ensures Celery discovers the tasks defined within the app structure.
# If running Celery worker from the workspace root, `backend.app.workers.tasks` might be needed.
# If running from `backend` dir, `app.workers.tasks` might work.
# Using the full path relative to the likely execution root (workspace) is safer.
try:
    # Option 1: If worker runs from workspace root
    import backend.app.workers.tasks
except ImportError:
    try:
        # Option 2: If worker runs from backend directory
        import app.workers.tasks
    except ImportError:
        logger.error("Could not import Celery tasks. Ensure worker is run from workspace root or backend directory.") 
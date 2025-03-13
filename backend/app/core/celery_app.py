"""
Celery app configuration using PostgreSQL as broker and result backend.
"""
import os
from celery import Celery
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Celery configuration from environment variables
broker_url = os.getenv("CELERY_BROKER_URL")
result_backend = os.getenv("CELERY_RESULT_BACKEND")

if not broker_url or not result_backend:
    raise ValueError(
        "Celery configuration not found. Please set CELERY_BROKER_URL and CELERY_RESULT_BACKEND environment variables."
    )

# Create Celery app
celery_app = Celery(
    "austin_property_map",
    broker=broker_url,
    backend=result_backend,
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Chicago",  # Austin timezone
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    worker_max_tasks_per_child=1000,
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=None,  # Retry forever
    task_acks_late=True,  # Acknowledge tasks after execution (better for reliability)
    task_reject_on_worker_lost=True,  # Reject tasks if worker is lost
    worker_prefetch_multiplier=1,  # Prefetch only one task at a time (better for long-running tasks)
)

# Configure task routes
celery_app.conf.task_routes = {
    "app.tasks.property_tasks.*": {"queue": "property_tasks"},
    "app.tasks.neo4j_sync_tasks.*": {"queue": "neo4j_sync"},
}

# Optional: Configure task default rate limits
celery_app.conf.task_default_rate_limit = "10/m"  # 10 tasks per minute by default 
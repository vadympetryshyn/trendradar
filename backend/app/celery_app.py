import os

from celery import Celery

broker_url = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")

celery_app = Celery(
    "trendsradar",
    broker=broker_url,
    backend=result_backend,
)

celery_app.autodiscover_tasks(["app.tasks"])

celery_app.conf.timezone = "UTC"
celery_app.conf.beat_schedule = {
    "check-scheduled-analyses": {
        "task": "app.tasks.run_scheduled_analyses",
        "schedule": 300.0,  # every 5 minutes
    },
}

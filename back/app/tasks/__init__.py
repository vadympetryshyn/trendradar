import logging
from datetime import datetime, timedelta, timezone

from celery.signals import worker_process_init, worker_ready

from app.celery_app import celery_app
from app.database import SessionLocal, engine

logger = logging.getLogger(__name__)

# Maximum age (minutes) before a running/queued task is considered stuck
STALE_TASK_TIMEOUT_MINUTES = 10


@worker_process_init.connect
def reset_db_connections(**kwargs):
    """Dispose inherited DB connections after prefork so each worker gets fresh ones."""
    engine.dispose()
    logger.info("Worker process: disposed inherited DB connections")


@worker_ready.connect
def cleanup_stale_tasks_on_startup(**kwargs):
    """Clear any stuck tasks when the worker starts (e.g. after container rebuild)."""
    from app.models import CollectionTask

    db = SessionLocal()
    try:
        stuck = (
            db.query(CollectionTask)
            .filter(CollectionTask.status.in_(["running", "queued"]))
            .all()
        )
        if not stuck:
            logger.info("Worker startup: no stuck tasks found")
            return

        count = (
            db.query(CollectionTask)
            .filter(CollectionTask.status.in_(["running", "queued"]))
            .update({
                CollectionTask.status: "failed",
                CollectionTask.error_message: "Auto-cleared on worker startup (container restart)",
                CollectionTask.completed_at: datetime.now(timezone.utc),
            })
        )
        db.commit()
        logger.info(f"Worker startup: cleared {count} stuck tasks")
    except Exception as e:
        logger.error(f"Worker startup cleanup failed: {e}")
        db.rollback()
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=2, default_retry_delay=60, soft_time_limit=600, time_limit=660)
def collect_niche_trends(self, niche_id: int, task_record_id: int | None = None, collection_type: str = "now"):
    from app.models import CollectionTask, ScheduleConfig
    from app.services.trend_collection_service import TrendCollectionService

    db = SessionLocal()
    try:
        # Get or create task record
        task_record = None
        if task_record_id:
            task_record = db.query(CollectionTask).filter(CollectionTask.id == task_record_id).first()

        if not task_record:
            task_record = CollectionTask(
                niche_id=niche_id,
                collection_type=collection_type,
                celery_task_id=self.request.id,
                status="running",
            )
            db.add(task_record)
            db.commit()
            db.refresh(task_record)

        # Update status to running
        task_record.status = "running"
        task_record.celery_task_id = self.request.id
        db.commit()

        logger.info(
            f"[Niche {niche_id}] Starting trend collection task "
            f"(collection_type={collection_type}, celery_id={self.request.id})"
        )

        service = TrendCollectionService(db)
        result = service.collect_trends(niche_id, collection_type=collection_type)

        # Update task record with results
        task_record.status = "completed"
        task_record.trends_created = result.get("created", 0)
        task_record.trends_expired = result.get("expired", 0)
        task_record.completed_at = datetime.now(timezone.utc)
        db.commit()

        # Update schedule last_run_at only for the matching collection_type
        schedule = (
            db.query(ScheduleConfig)
            .filter(
                ScheduleConfig.niche_id == niche_id,
                ScheduleConfig.collection_type == collection_type,
            )
            .first()
        )
        if schedule:
            schedule.last_run_at = datetime.now(timezone.utc)
            db.commit()

        logger.info(f"Collection completed for niche {niche_id} ({collection_type}): {result}")
        return {"niche_id": niche_id, "collection_type": collection_type, "status": "completed", **result}

    except Exception as exc:
        logger.error(f"Collection failed for niche {niche_id} ({collection_type}): {exc}")

        # Update task record with failure
        try:
            db.rollback()
            if task_record:
                task_record = db.query(CollectionTask).filter(CollectionTask.id == task_record.id).first()
                if task_record:
                    task_record.status = "failed"
                    task_record.error_message = str(exc)[:500]
                    task_record.completed_at = datetime.now(timezone.utc)
                    db.commit()
        except Exception as inner_exc:
            logger.error(f"Failed to update task record for niche {niche_id}: {inner_exc}")

        try:
            self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for niche {niche_id}")
            return {"status": "failed", "error": str(exc)}
    finally:
        db.close()


@celery_app.task
def run_scheduled_collections():
    from app.models import CollectionTask, ScheduleConfig

    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)

        # Auto-clear tasks stuck longer than the timeout
        stale_cutoff = now - timedelta(minutes=STALE_TASK_TIMEOUT_MINUTES)
        stale_count = (
            db.query(CollectionTask)
            .filter(
                CollectionTask.status.in_(["running", "queued"]),
                CollectionTask.started_at < stale_cutoff,
            )
            .update({
                CollectionTask.status: "failed",
                CollectionTask.error_message: f"Auto-cleared: stuck for >{STALE_TASK_TIMEOUT_MINUTES}min",
                CollectionTask.completed_at: now,
            })
        )
        if stale_count:
            db.commit()
            logger.info(f"Auto-cleared {stale_count} stale tasks (>{STALE_TASK_TIMEOUT_MINUTES}min old)")

        configs = (
            db.query(ScheduleConfig)
            .filter(ScheduleConfig.is_enabled.is_(True))
            .all()
        )

        dispatched = 0

        for config in configs:
            if config.last_run_at is None:
                should_run = True
            else:
                elapsed = (now - config.last_run_at).total_seconds() / 60
                should_run = elapsed >= config.interval_minutes

            if not should_run:
                continue

            # Skip if a task is already running/queued for this niche+collection_type
            existing = (
                db.query(CollectionTask)
                .filter(
                    CollectionTask.niche_id == config.niche_id,
                    CollectionTask.collection_type == config.collection_type,
                    CollectionTask.status.in_(["queued", "running"]),
                )
                .first()
            )
            if existing:
                logger.info(
                    f"Skipping niche {config.niche_id} ({config.collection_type}): "
                    f"task #{existing.id} already {existing.status}"
                )
                continue

            # Create task record first
            task_record = CollectionTask(
                niche_id=config.niche_id,
                collection_type=config.collection_type,
                status="queued",
            )
            db.add(task_record)
            db.commit()
            db.refresh(task_record)

            collect_niche_trends.delay(config.niche_id, task_record.id, config.collection_type)
            dispatched += 1
            logger.info(
                f"Dispatched collection for niche {config.niche_id} "
                f"(collection_type={config.collection_type})"
            )

        logger.info(f"Scheduled check complete: {dispatched} collections dispatched")
        return {"dispatched": dispatched}

    finally:
        db.close()


@celery_app.task
def cleanup_expired_trends():
    from app.models import Trend

    db = SessionLocal()
    try:
        deleted = (
            db.query(Trend)
            .filter(Trend.status == "expired")
            .delete()
        )
        db.commit()
        logger.info(f"Cleanup: deleted {deleted} expired trends")
        return {"deleted": deleted}
    finally:
        db.close()

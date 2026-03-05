import logging
from datetime import datetime, timedelta, timezone

from app.celery_app import celery_app
from app.database import SessionLocal

logger = logging.getLogger(__name__)


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

        # Dispatch rising detection as a separate task after "now" collections
        if collection_type == "now":
            collect_rising_trends.delay(niche_id)
            logger.info(f"[Niche {niche_id}] Dispatched rising trend detection task")

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
        configs = (
            db.query(ScheduleConfig)
            .filter(ScheduleConfig.is_enabled.is_(True))
            .all()
        )

        now = datetime.now(timezone.utc)
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


@celery_app.task(bind=True, max_retries=1, default_retry_delay=60, soft_time_limit=300, time_limit=360)
def collect_rising_trends(self, niche_id: int):
    from app.services.trend_collection_service import TrendCollectionService

    db = SessionLocal()
    try:
        logger.info(f"[Niche {niche_id}] Starting rising trend collection task (celery_id={self.request.id})")
        service = TrendCollectionService(db)
        result = service.collect_rising_trends(niche_id)
        logger.info(f"Rising collection completed for niche {niche_id}: {result}")
        return {"niche_id": niche_id, "collection_type": "rising", "status": "completed", **result}
    except Exception as exc:
        logger.error(f"Rising collection failed for niche {niche_id}: {exc}")
        try:
            self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for rising collection niche {niche_id}")
            return {"status": "failed", "error": str(exc)}
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

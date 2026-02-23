import logging
from datetime import datetime, timedelta, timezone

from app.celery_app import celery_app
from app.database import SessionLocal

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=300)
def collect_niche_trends(self, niche_id: int, task_record_id: int | None = None):
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

        logger.info(f"[Niche {niche_id}] Starting trend collection task (celery_id={self.request.id})")

        service = TrendCollectionService(db)
        result = service.collect_trends(niche_id)

        # Update task record with results
        task_record.status = "completed"
        task_record.trends_created = result.get("created", 0)
        task_record.trends_expired = result.get("expired", 0)
        task_record.completed_at = datetime.now(timezone.utc)
        db.commit()

        # Update schedule last_run_at
        schedules = db.query(ScheduleConfig).filter(ScheduleConfig.niche_id == niche_id).all()
        if schedules:
            for schedule in schedules:
                schedule.last_run_at = datetime.now(timezone.utc)
            db.commit()

        logger.info(f"Collection completed for niche {niche_id}: {result}")
        return {"niche_id": niche_id, "status": "completed", **result}

    except Exception as exc:
        logger.error(f"Collection failed for niche {niche_id}: {exc}")

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

            if should_run:
                # Create task record first
                task_record = CollectionTask(
                    niche_id=config.niche_id,
                    status="queued",
                )
                db.add(task_record)
                db.commit()
                db.refresh(task_record)

                collect_niche_trends.delay(config.niche_id, task_record.id)
                dispatched += 1
                logger.info(f"Dispatched collection for niche {config.niche_id}")

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

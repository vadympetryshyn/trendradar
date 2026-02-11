import logging
from datetime import datetime, timezone

from app.celery_app import celery_app
from app.database import SessionLocal

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=300)
def analyze_niche_trends(self, niche_id: int):
    from app.models import ScheduleConfig
    from app.services.trend_analysis_service import TrendAnalysisService

    db = SessionLocal()
    try:
        service = TrendAnalysisService(db)
        analysis = service.run_analysis(niche_id, celery_task_id=self.request.id)

        schedules = db.query(ScheduleConfig).filter(ScheduleConfig.niche_id == niche_id).all()
        if schedules:
            for schedule in schedules:
                schedule.last_run_at = datetime.now(timezone.utc)
            db.commit()

        logger.info(f"Analysis {analysis.id} completed for niche {niche_id}")
        return {"analysis_id": analysis.id, "status": analysis.status}

    except Exception as exc:
        logger.error(f"Analysis failed for niche {niche_id}: {exc}")
        try:
            self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for niche {niche_id}")
            return {"status": "failed", "error": str(exc)}
    finally:
        db.close()


@celery_app.task
def run_scheduled_analyses():
    from app.models import ScheduleConfig

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
                analyze_niche_trends.delay(config.niche_id)
                dispatched += 1
                logger.info(f"Dispatched analysis for niche {config.niche_id}")

        logger.info(f"Scheduled check complete: {dispatched} analyses dispatched")
        return {"dispatched": dispatched}

    finally:
        db.close()

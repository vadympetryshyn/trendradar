from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Niche, ScheduleConfig, TrendAnalysis
from app.schemas import (
    AnalysisListItem,
    ManualTriggerResponse,
    PaginatedAnalysesResponse,
    PaginatedTasksResponse,
    ScheduleConfigCreate,
    ScheduleConfigResponse,
    ScheduleConfigUpdate,
    TaskListItem,
    TaskStatusResponse,
    TrendAnalysisResponse,
)

router = APIRouter(prefix="/admin", tags=["admin"])


def _schedule_to_response(config: ScheduleConfig) -> ScheduleConfigResponse:
    data = ScheduleConfigResponse.model_validate(config)
    data.next_run_at = config.next_run_at
    if config.niche:
        data.niche_name = config.niche.name
        data.niche_slug = config.niche.slug
    return data


@router.post("/analyze/{niche_slug}", response_model=ManualTriggerResponse)
def trigger_analysis(niche_slug: str, db: Session = Depends(get_db)):
    niche = db.query(Niche).filter(Niche.slug == niche_slug, Niche.is_active.is_(True)).first()
    if not niche:
        raise HTTPException(status_code=404, detail="Niche not found")

    from app.tasks import analyze_niche_trends

    result = analyze_niche_trends.delay(niche.id)

    return ManualTriggerResponse(
        task_id=result.id,
        message=f"Analysis triggered for niche '{niche.name}'",
        niche_slug=niche_slug,
    )


@router.post("/analyze-all")
def trigger_all_analyses(db: Session = Depends(get_db)):
    niches = db.query(Niche).filter(Niche.is_active.is_(True)).all()
    if not niches:
        raise HTTPException(status_code=404, detail="No active niches found")

    from app.tasks import analyze_niche_trends

    results = []
    for niche in niches:
        result = analyze_niche_trends.delay(niche.id)
        results.append({
            "task_id": result.id,
            "niche_slug": niche.slug,
            "niche_name": niche.name,
        })
    return {"triggered": len(results), "tasks": results}


@router.post("/task/{task_id}/stop")
def stop_task(task_id: str, db: Session = Depends(get_db)):
    from app.celery_app import celery_app

    celery_app.control.revoke(task_id, terminate=True, signal="SIGTERM")

    analysis = db.query(TrendAnalysis).filter(TrendAnalysis.celery_task_id == task_id).first()
    if analysis and analysis.status in ("pending", "queued", "fetching", "analyzing"):
        db.delete(analysis)
        db.commit()

    return {"detail": "Task stopped and cleaned up", "task_id": task_id}


@router.post("/tasks/stop-all")
def stop_all_tasks(db: Session = Depends(get_db)):
    from app.celery_app import celery_app

    active_analyses = (
        db.query(TrendAnalysis)
        .filter(TrendAnalysis.status.in_(["pending", "queued", "fetching", "analyzing"]))
        .all()
    )

    stopped = 0
    for analysis in active_analyses:
        if analysis.celery_task_id:
            celery_app.control.revoke(analysis.celery_task_id, terminate=True, signal="SIGTERM")
        db.delete(analysis)
        stopped += 1

    db.commit()
    return {"detail": f"Stopped {stopped} tasks", "stopped": stopped}


@router.get("/task/{task_id}/status", response_model=TaskStatusResponse)
def get_task_status(task_id: str, db: Session = Depends(get_db)):
    analysis = db.query(TrendAnalysis).filter(TrendAnalysis.celery_task_id == task_id).first()
    if analysis:
        return TaskStatusResponse(
            task_id=task_id,
            status=analysis.status,
            analysis_id=analysis.id,
            posts_fetched=analysis.posts_fetched,
            subreddits_fetched=analysis.subreddits_fetched,
            error_message=analysis.error_message,
            started_at=analysis.started_at,
            completed_at=analysis.completed_at,
        )

    from app.celery_app import celery_app

    result = celery_app.AsyncResult(task_id)
    celery_state = result.state if result.state else "PENDING"
    status_map = {"PENDING": "queued", "STARTED": "pending", "RETRY": "pending"}
    return TaskStatusResponse(
        task_id=task_id,
        status=status_map.get(celery_state, "queued"),
    )


@router.get("/schedules", response_model=list[ScheduleConfigResponse])
def list_schedules(db: Session = Depends(get_db)):
    configs = db.query(ScheduleConfig).all()
    return [_schedule_to_response(config) for config in configs]


@router.post("/schedules", response_model=ScheduleConfigResponse, status_code=201)
def create_schedule(payload: ScheduleConfigCreate, db: Session = Depends(get_db)):
    niche = db.query(Niche).filter(Niche.id == payload.niche_id).first()
    if not niche:
        raise HTTPException(status_code=404, detail="Niche not found")

    config = ScheduleConfig(
        niche_id=payload.niche_id,
        interval_minutes=payload.interval_minutes,
        is_enabled=payload.is_enabled,
        updated_at=datetime.now(timezone.utc),
    )
    db.add(config)
    db.commit()
    db.refresh(config)

    return _schedule_to_response(config)


@router.put("/schedules/{schedule_id}", response_model=ScheduleConfigResponse)
def update_schedule(schedule_id: int, update: ScheduleConfigUpdate, db: Session = Depends(get_db)):
    config = db.query(ScheduleConfig).filter(ScheduleConfig.id == schedule_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Schedule not found")

    if update.interval_minutes is not None:
        config.interval_minutes = update.interval_minutes
    if update.is_enabled is not None:
        config.is_enabled = update.is_enabled
    config.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(config)

    return _schedule_to_response(config)


@router.delete("/schedules/{schedule_id}")
def delete_schedule(schedule_id: int, db: Session = Depends(get_db)):
    config = db.query(ScheduleConfig).filter(ScheduleConfig.id == schedule_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Schedule not found")

    db.delete(config)
    db.commit()
    return {"detail": "Schedule deleted"}


@router.get("/analyses", response_model=PaginatedAnalysesResponse)
def list_analyses(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(TrendAnalysis).join(Niche)
    if status:
        query = query.filter(TrendAnalysis.status == status)
    total = query.count()
    analyses = (
        query.order_by(TrendAnalysis.started_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    items = [
        AnalysisListItem(
            id=a.id,
            niche_name=a.niche.name,
            niche_slug=a.niche.slug,
            status=a.status,
            overall_summary=a.overall_summary,
            posts_fetched=a.posts_fetched,
            subreddits_fetched=a.subreddits_fetched,
            error_message=a.error_message,
            celery_task_id=a.celery_task_id,
            started_at=a.started_at,
            completed_at=a.completed_at,
            trend_items_count=len(a.trend_items),
        )
        for a in analyses
    ]
    return PaginatedAnalysesResponse(items=items, total=total, page=page, per_page=per_page)


@router.get("/analyses/{analysis_id}", response_model=TrendAnalysisResponse)
def get_analysis(analysis_id: int, db: Session = Depends(get_db)):
    analysis = db.query(TrendAnalysis).filter(TrendAnalysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis


@router.delete("/analyses/{analysis_id}")
def delete_analysis(analysis_id: int, db: Session = Depends(get_db)):
    analysis = db.query(TrendAnalysis).filter(TrendAnalysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    db.delete(analysis)
    db.commit()
    return {"detail": "Analysis deleted"}


@router.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    analysis = db.query(TrendAnalysis).filter(TrendAnalysis.id == task_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(analysis)
    db.commit()
    return {"detail": "Task deleted"}


@router.get("/tasks", response_model=PaginatedTasksResponse)
def list_tasks(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    total = db.query(func.count(TrendAnalysis.id)).scalar()
    analyses = (
        db.query(TrendAnalysis)
        .join(Niche)
        .order_by(TrendAnalysis.started_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    items = [
        TaskListItem(
            id=a.id,
            celery_task_id=a.celery_task_id,
            niche_name=a.niche.name,
            niche_slug=a.niche.slug,
            status=a.status,
            posts_fetched=a.posts_fetched,
            subreddits_fetched=a.subreddits_fetched,
            error_message=a.error_message,
            started_at=a.started_at,
            completed_at=a.completed_at,
        )
        for a in analyses
    ]
    return PaginatedTasksResponse(items=items, total=total, page=page, per_page=per_page)

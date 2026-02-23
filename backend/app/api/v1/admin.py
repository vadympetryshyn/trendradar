from datetime import datetime, timezone

from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CollectionTask, Niche, ScheduleConfig, Trend
from app.schemas import (
    CollectionTaskListResponse,
    CollectionTaskResponse,
    DashboardStatsResponse,
    ManualTriggerResponse,
    NicheScheduleStatus,
    SchedulerRunRequest,
    SchedulerStartRequest,
    SchedulerStatusResponse,
)

router = APIRouter(prefix="/admin", tags=["admin"])


def _task_to_response(task: CollectionTask) -> CollectionTaskResponse:
    niche = task.niche
    return CollectionTaskResponse(
        id=task.id,
        niche_id=task.niche_id,
        niche_name=niche.name if niche else f"Niche #{task.niche_id}",
        niche_slug=niche.slug if niche else "",
        celery_task_id=task.celery_task_id,
        status=task.status,
        trends_created=task.trends_created,
        trends_expired=task.trends_expired,
        error_message=task.error_message,
        started_at=task.started_at,
        completed_at=task.completed_at,
    )


def _build_niche_schedule_status(
    config: ScheduleConfig, trend_count: int
) -> NicheScheduleStatus:
    niche = config.niche
    return NicheScheduleStatus(
        niche_id=config.niche_id,
        niche_name=niche.name if niche else f"Niche #{config.niche_id}",
        niche_slug=niche.slug if niche else "",
        is_enabled=config.is_enabled,
        interval_minutes=config.interval_minutes,
        last_run_at=config.last_run_at,
        next_run_at=config.next_run_at,
        trend_count=trend_count,
    )


# ── Scheduler endpoints ──────────────────────────────────────────────


@router.get("/scheduler/status", response_model=SchedulerStatusResponse)
def get_scheduler_status(db: Session = Depends(get_db)):
    configs = (
        db.query(ScheduleConfig)
        .join(Niche)
        .filter(Niche.is_active.is_(True))
        .all()
    )
    any_running = any(c.is_enabled for c in configs)

    # Single grouped query instead of N+1
    trend_counts = dict(
        db.query(Trend.niche_id, func.count(Trend.id))
        .filter(Trend.status == "active")
        .group_by(Trend.niche_id)
        .all()
    )

    niches_status = [
        _build_niche_schedule_status(config, trend_counts.get(config.niche_id, 0))
        for config in configs
    ]

    return SchedulerStatusResponse(running=any_running, niches=niches_status)


@router.post("/scheduler/start", response_model=SchedulerStatusResponse)
def start_scheduler(
    request: SchedulerStartRequest,
    db: Session = Depends(get_db),
):
    (
        db.query(ScheduleConfig)
        .filter(
            ScheduleConfig.niche_id.in_(
                db.query(Niche.id).filter(Niche.is_active.is_(True))
            )
        )
        .update(
            {
                ScheduleConfig.is_enabled: True,
                ScheduleConfig.interval_minutes: request.interval_minutes,
                ScheduleConfig.updated_at: datetime.now(timezone.utc),
            },
            synchronize_session="fetch",
        )
    )
    db.commit()

    return get_scheduler_status(db)


@router.post("/scheduler/stop", response_model=SchedulerStatusResponse)
def stop_scheduler(db: Session = Depends(get_db)):
    (
        db.query(ScheduleConfig)
        .filter(
            ScheduleConfig.niche_id.in_(
                db.query(Niche.id).filter(Niche.is_active.is_(True))
            )
        )
        .update(
            {
                ScheduleConfig.is_enabled: False,
                ScheduleConfig.updated_at: datetime.now(timezone.utc),
            },
            synchronize_session="fetch",
        )
    )
    db.commit()

    return get_scheduler_status(db)


@router.post("/scheduler/run", response_model=ManualTriggerResponse)
def manual_run(
    request: SchedulerRunRequest = SchedulerRunRequest(),
    db: Session = Depends(get_db),
):
    from app.tasks import collect_niche_trends

    if request.niche_id is not None:
        niche = db.query(Niche).filter(Niche.id == request.niche_id).first()
        if not niche:
            raise HTTPException(status_code=404, detail="Niche not found")

        task_record = CollectionTask(niche_id=niche.id, status="queued")
        db.add(task_record)
        db.commit()
        db.refresh(task_record)

        collect_niche_trends.delay(niche.id, task_record.id)
        return ManualTriggerResponse(
            message=f"Collection triggered for '{niche.name}'",
            niche_id=niche.id,
            niche_name=niche.name,
        )

    niches = db.query(Niche).filter(Niche.is_active.is_(True)).all()
    if not niches:
        raise HTTPException(status_code=404, detail="No active niches found")

    for niche in niches:
        task_record = CollectionTask(niche_id=niche.id, status="queued")
        db.add(task_record)
        db.commit()
        db.refresh(task_record)
        collect_niche_trends.delay(niche.id, task_record.id)

    return ManualTriggerResponse(
        message=f"Collection triggered for {len(niches)} niches",
    )


@router.post("/scheduler/niche/{niche_id}/start", response_model=NicheScheduleStatus)
def start_niche_schedule(niche_id: int, db: Session = Depends(get_db)):
    config = db.query(ScheduleConfig).filter(ScheduleConfig.niche_id == niche_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Schedule not found for this niche")

    config.is_enabled = True
    config.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(config)

    trend_count = (
        db.query(func.count(Trend.id))
        .filter(Trend.niche_id == niche_id, Trend.status == "active")
        .scalar()
    )

    return _build_niche_schedule_status(config, trend_count)


@router.post("/scheduler/niche/{niche_id}/stop", response_model=NicheScheduleStatus)
def stop_niche_schedule(niche_id: int, db: Session = Depends(get_db)):
    config = db.query(ScheduleConfig).filter(ScheduleConfig.niche_id == niche_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Schedule not found for this niche")

    config.is_enabled = False
    config.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(config)

    trend_count = (
        db.query(func.count(Trend.id))
        .filter(Trend.niche_id == niche_id, Trend.status == "active")
        .scalar()
    )

    return _build_niche_schedule_status(config, trend_count)


# ── Task endpoints ────────────────────────────────────────────────────


@router.get("/tasks", response_model=CollectionTaskListResponse)
def list_tasks(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(CollectionTask)
    if status:
        query = query.filter(CollectionTask.status == status)
    total = query.count()
    tasks = (
        query.order_by(CollectionTask.started_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return CollectionTaskListResponse(
        items=[_task_to_response(t) for t in tasks],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/tasks/{task_id}", response_model=CollectionTaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(CollectionTask).filter(CollectionTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return _task_to_response(task)


@router.post("/tasks/{task_id}/stop")
def stop_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(CollectionTask).filter(CollectionTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status in ("queued", "running"):
        # Revoke celery task if possible
        if task.celery_task_id:
            from app.celery_app import celery_app
            celery_app.control.revoke(task.celery_task_id, terminate=True, signal="SIGTERM")

        task.status = "stopped"
        task.completed_at = datetime.now(timezone.utc)
        db.commit()

    return _task_to_response(task)


@router.delete("/tasks/bulk")
def delete_tasks_bulk(
    ids: List[int] = Body(..., embed=True),
    db: Session = Depends(get_db),
):
    tasks = db.query(CollectionTask).filter(CollectionTask.id.in_(ids)).all()
    if not tasks:
        raise HTTPException(status_code=404, detail="No tasks found")

    for task in tasks:
        if task.status in ("queued", "running") and task.celery_task_id:
            from app.celery_app import celery_app
            celery_app.control.revoke(task.celery_task_id, terminate=True, signal="SIGTERM")
        db.delete(task)

    db.commit()
    return {"detail": f"{len(tasks)} task(s) deleted"}


@router.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(CollectionTask).filter(CollectionTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Stop if still running
    if task.status in ("queued", "running") and task.celery_task_id:
        from app.celery_app import celery_app
        celery_app.control.revoke(task.celery_task_id, terminate=True, signal="SIGTERM")

    db.delete(task)
    db.commit()
    return {"detail": "Task deleted"}


# ── Trend cleanup endpoint ────────────────────────────────────────────


@router.delete("/trends/expired")
def delete_expired_trends(db: Session = Depends(get_db)):
    deleted = db.query(Trend).filter(Trend.status == "expired").delete()
    db.commit()
    return {"detail": f"{deleted} expired trend(s) deleted"}


# ── Stats endpoint ────────────────────────────────────────────────────


@router.get("/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(db: Session = Depends(get_db)):
    trend_stats = db.query(
        func.count(case((Trend.status == "active", Trend.id))),
        func.count(case((Trend.status == "expired", Trend.id))),
        func.count(case((
            (Trend.status == "active") & (Trend.research_done.is_(True)),
            Trend.id,
        ))),
        func.count(case((
            (Trend.status == "active") & (Trend.embedding.isnot(None)),
            Trend.id,
        ))),
    ).first()

    total_niches = db.query(func.count(Niche.id)).filter(Niche.is_active.is_(True)).scalar()

    return DashboardStatsResponse(
        active_trends=trend_stats[0],
        expired_trends=trend_stats[1],
        researched_trends=trend_stats[2],
        embedded_trends=trend_stats[3],
        total_niches=total_niches,
    )

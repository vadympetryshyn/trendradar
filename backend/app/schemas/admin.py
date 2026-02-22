from datetime import datetime

from pydantic import BaseModel


class NicheScheduleStatus(BaseModel):
    niche_id: int
    niche_name: str
    niche_slug: str
    is_enabled: bool
    interval_minutes: int
    last_run_at: datetime | None
    next_run_at: datetime | None
    trend_count: int = 0


class SchedulerStatusResponse(BaseModel):
    running: bool
    niches: list[NicheScheduleStatus]


class SchedulerStartRequest(BaseModel):
    interval_minutes: int = 60


class SchedulerRunRequest(BaseModel):
    niche_id: int | None = None


class ManualTriggerResponse(BaseModel):
    message: str
    niche_id: int | None = None
    niche_name: str | None = None


class DashboardStatsResponse(BaseModel):
    active_trends: int
    expired_trends: int
    researched_trends: int
    embedded_trends: int
    total_niches: int

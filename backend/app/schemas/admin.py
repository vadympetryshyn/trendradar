from datetime import datetime

from pydantic import BaseModel


class ManualTriggerResponse(BaseModel):
    task_id: str
    message: str
    niche_slug: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    analysis_id: int | None = None
    posts_fetched: int = 0
    subreddits_fetched: int = 0
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class AnalysisListItem(BaseModel):
    id: int
    niche_name: str
    niche_slug: str
    status: str
    overall_summary: str | None = None
    posts_fetched: int = 0
    subreddits_fetched: int = 0
    error_message: str | None = None
    celery_task_id: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    trend_items_count: int = 0


class PaginatedAnalysesResponse(BaseModel):
    items: list[AnalysisListItem]
    total: int
    page: int
    per_page: int


class TaskListItem(BaseModel):
    id: int
    celery_task_id: str | None = None
    niche_name: str
    niche_slug: str
    status: str
    posts_fetched: int = 0
    subreddits_fetched: int = 0
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class PaginatedTasksResponse(BaseModel):
    items: list[TaskListItem]
    total: int
    page: int
    per_page: int

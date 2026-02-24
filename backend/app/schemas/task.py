from datetime import datetime

from pydantic import BaseModel


class CollectionTaskResponse(BaseModel):
    id: int
    niche_id: int
    niche_name: str
    niche_slug: str
    collection_type: str = "now"
    celery_task_id: str | None
    status: str
    trends_created: int
    trends_expired: int
    error_message: str | None
    started_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class CollectionTaskListResponse(BaseModel):
    items: list[CollectionTaskResponse]
    total: int
    page: int
    per_page: int

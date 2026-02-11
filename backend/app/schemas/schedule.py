from datetime import datetime

from pydantic import BaseModel, Field


class ScheduleConfigResponse(BaseModel):
    id: int
    niche_id: int
    niche_name: str | None = None
    niche_slug: str | None = None
    interval_minutes: int
    is_enabled: bool
    last_run_at: datetime | None
    next_run_at: datetime | None = None
    updated_at: datetime

    model_config = {"from_attributes": True}


class ScheduleConfigUpdate(BaseModel):
    interval_minutes: int | None = Field(None, ge=15, le=1440)
    is_enabled: bool | None = None


class ScheduleConfigCreate(BaseModel):
    niche_id: int
    interval_minutes: int = Field(60, ge=15, le=1440)
    is_enabled: bool = True

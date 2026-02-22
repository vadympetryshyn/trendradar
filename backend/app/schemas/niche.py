from datetime import datetime

from pydantic import BaseModel


class NicheResponse(BaseModel):
    id: int
    name: str
    slug: str
    subreddits: list[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class NicheDetailResponse(BaseModel):
    id: int
    name: str
    slug: str
    subreddits: list[str]
    is_active: bool
    created_at: datetime
    active_trend_count: int = 0
    expired_trend_count: int = 0

    model_config = {"from_attributes": True}

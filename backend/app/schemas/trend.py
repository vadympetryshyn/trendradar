from datetime import datetime

from pydantic import BaseModel


class TrendItemResponse(BaseModel):
    id: int
    title: str
    summary: str
    sentiment: str
    sentiment_score: float
    category: str
    key_points: list[str]
    source_urls: list[str]
    source_subreddits: list[str]
    mention_count: int
    relevance_score: float

    model_config = {"from_attributes": True}


class TrendAnalysisResponse(BaseModel):
    id: int
    niche_id: int
    status: str
    overall_summary: str | None
    posts_fetched: int
    subreddits_fetched: int
    error_message: str | None
    started_at: datetime
    completed_at: datetime | None
    trend_items: list[TrendItemResponse]

    model_config = {"from_attributes": True}


class TrendAnalysisSummaryResponse(BaseModel):
    id: int
    niche_id: int
    status: str
    overall_summary: str | None
    posts_fetched: int
    subreddits_fetched: int
    error_message: str | None
    started_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class PaginatedHistoryResponse(BaseModel):
    items: list[TrendAnalysisSummaryResponse]
    total: int
    page: int
    per_page: int

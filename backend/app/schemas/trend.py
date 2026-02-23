from datetime import datetime

from pydantic import BaseModel


class TrendListItem(BaseModel):
    id: str
    niche_id: int
    title: str
    summary: str
    trend_type: str
    status: str
    sentiment: str
    sentiment_score: float
    category: str
    key_points: list[str]
    source_urls: list[str]
    source_subreddits: list[str]
    mention_count: int
    relevance_score: float
    research_done: bool
    has_embedding: bool
    collected_at: datetime

    model_config = {"from_attributes": True}


class TrendDetail(BaseModel):
    id: str
    niche_id: int
    title: str
    summary: str
    trend_type: str
    status: str
    sentiment: str
    sentiment_score: float
    category: str
    key_points: list[str]
    source_urls: list[str]
    source_subreddits: list[str]
    mention_count: int
    relevance_score: float
    context_summary: str | None
    research_citations: list[str]
    research_done: bool
    has_embedding: bool
    researched_at: datetime | None
    collected_at: datetime
    expired_at: datetime | None

    model_config = {"from_attributes": True}


class TrendListResponse(BaseModel):
    items: list[TrendListItem]
    total: int
    limit: int
    offset: int


class TrendSearchRequest(BaseModel):
    query: str
    niche_id: int | None = None
    limit: int = 10


class TrendSearchResult(BaseModel):
    id: str
    title: str
    summary: str
    trend_type: str
    sentiment: str
    category: str
    relevance_score: float
    similarity: float
    collected_at: datetime

    model_config = {"from_attributes": True}


class TrendSearchResponse(BaseModel):
    results: list[TrendSearchResult]
    query: str

from datetime import datetime

from pydantic import BaseModel, field_validator


class TrendListItem(BaseModel):
    id: str
    niche_id: int
    title: str
    summary: str
    source_post_ids: list[str] = []
    status: str
    sentiment: str
    category: str
    key_points: list[str]
    source_urls: list[str]
    mention_urls: list[str] = []
    source_subreddits: list[str]
    mention_count: int
    relevance_score: float
    collection_type: str
    research_done: bool
    has_embedding: bool
    collected_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("id", mode="before")
    @classmethod
    def stringify_id(cls, v: object) -> str:
        return str(v)


class TrendDetail(BaseModel):
    id: str
    niche_id: int
    title: str
    summary: str
    source_post_ids: list[str] = []
    status: str
    sentiment: str
    category: str
    key_points: list[str]
    source_urls: list[str]
    mention_urls: list[str] = []
    source_subreddits: list[str]
    mention_count: int
    relevance_score: float
    collection_type: str
    context_summary: str | None
    research_citations: list[str]
    research_done: bool
    has_embedding: bool
    researched_at: datetime | None
    collected_at: datetime
    expired_at: datetime | None

    model_config = {"from_attributes": True}

    @field_validator("id", mode="before")
    @classmethod
    def stringify_id(cls, v: object) -> str:
        return str(v)


class TrendListResponse(BaseModel):
    items: list[TrendListItem]
    total: int
    limit: int
    offset: int


class TrendSearchRequest(BaseModel):
    query: str
    niche: str | None = None
    limit: int = 10


class TrendSearchResult(BaseModel):
    id: str
    title: str
    summary: str
    source_post_ids: list[str] = []
    sentiment: str
    category: str
    relevance_score: float
    collection_type: str = "now"
    similarity: float
    collected_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("id", mode="before")
    @classmethod
    def stringify_id(cls, v: object) -> str:
        return str(v)


class TrendSearchResponse(BaseModel):
    results: list[TrendSearchResult]
    query: str

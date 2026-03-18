from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ExternalTrendListItem(BaseModel):
    id: str
    niche_id: int
    title: str
    summary: str
    status: str
    sentiment: str
    category: str
    key_points: list[str]
    relevance_score: float
    collection_type: str
    research_done: bool
    collected_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("id", mode="before")
    @classmethod
    def stringify_id(cls, v: object) -> str:
        return str(v)


class ExternalTrendDetail(BaseModel):
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
    collected_at: datetime
    context_summary: str | None
    research_citations: list[str]
    researched_at: datetime | None
    expired_at: datetime | None

    model_config = {"from_attributes": True}

    @field_validator("id", mode="before")
    @classmethod
    def stringify_id(cls, v: object) -> str:
        return str(v)


class ExternalTrendListResponse(BaseModel):
    items: list[ExternalTrendListItem]
    total: int
    limit: int
    offset: int


class ExternalTrendSearchResult(BaseModel):
    id: str
    title: str
    summary: str
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


class ExternalTrendSearchResponse(BaseModel):
    results: list[ExternalTrendSearchResult]
    query: str


class VectorSearchRequest(BaseModel):
    embedding: list[float]
    collection_types: list[str] = ["now", "daily"]
    niche: str | None = None
    limit: int = Field(5, ge=1, le=20)
    random: int | None = Field(None, ge=1, le=10)


class ExternalNicheResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: str = ""
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}

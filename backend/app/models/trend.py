import uuid
from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Trend(Base):
    __tablename__ = "trends"
    __table_args__ = (
        Index("ix_trends_niche_id_status", "niche_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    niche_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("niches.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    source_post_ids: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", index=True)
    sentiment: Mapped[str] = mapped_column(String(20), nullable=False, default="neutral")
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="General")
    key_points: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    source_urls: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    source_subreddits: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    mention_count: Mapped[int] = mapped_column(Integer, default=0)
    relevance_score: Mapped[float] = mapped_column(Float, default=0.0)
    context_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    research_citations: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    research_done: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    researched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    embedding = mapped_column(Vector(1536), nullable=True)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    expired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    niche = relationship("Niche", back_populates="trends")

    @property
    def has_embedding(self) -> bool:
        return self.embedding is not None

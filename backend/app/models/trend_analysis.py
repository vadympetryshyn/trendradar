from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TrendAnalysis(Base):
    __tablename__ = "trend_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    niche_id: Mapped[int] = mapped_column(Integer, ForeignKey("niches.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    overall_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    posts_fetched: Mapped[int] = mapped_column(Integer, default=0)
    subreddits_fetched: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    niche = relationship("Niche", back_populates="analyses")
    trend_items = relationship("TrendItem", back_populates="analysis", cascade="all, delete-orphan")

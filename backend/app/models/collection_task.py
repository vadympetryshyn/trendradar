from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CollectionTask(Base):
    __tablename__ = "collection_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    niche_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("niches.id"), nullable=False, index=True
    )
    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="queued")
    trends_created: Mapped[int] = mapped_column(Integer, default=0)
    trends_expired: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    niche = relationship("Niche")

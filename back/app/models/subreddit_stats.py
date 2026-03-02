from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SubredditStats(Base):
    __tablename__ = "subreddit_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subreddit: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    avg_score: Mapped[float] = mapped_column(Float, default=0.0)
    avg_comments: Mapped[float] = mapped_column(Float, default=0.0)
    avg_age_hours: Mapped[float] = mapped_column(Float, default=0.0)
    avg_velocity: Mapped[float] = mapped_column(Float, default=0.0)
    post_count: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

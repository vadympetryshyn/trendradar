from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TrendItem(Base):
    __tablename__ = "trend_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analysis_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("trend_analyses.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    sentiment: Mapped[str] = mapped_column(String(20), nullable=False)
    sentiment_score: Mapped[float] = mapped_column(Float, default=0.0)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    key_points: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    source_urls: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    source_subreddits: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    mention_count: Mapped[int] = mapped_column(Integer, default=0)
    relevance_score: Mapped[float] = mapped_column(Float, default=0.0)

    analysis = relationship("TrendAnalysis", back_populates="trend_items")

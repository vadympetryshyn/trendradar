from datetime import datetime, timedelta, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ScheduleConfig(Base):
    __tablename__ = "schedule_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    niche_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("niches.id"), nullable=False, index=True
    )
    interval_minutes: Mapped[int] = mapped_column(Integer, default=60)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    niche = relationship("Niche", back_populates="schedule_configs")

    @property
    def next_run_at(self) -> datetime | None:
        if not self.is_enabled:
            return None
        if self.last_run_at is None:
            return datetime.now(timezone.utc)
        return self.last_run_at + timedelta(minutes=self.interval_minutes)

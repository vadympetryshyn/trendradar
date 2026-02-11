import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import Niche, ScheduleConfig

NICHES_CONFIG = Path(__file__).resolve().parent / "niches.json"


def seed_data(db: Session):
    if not NICHES_CONFIG.exists():
        return

    niches_data = json.loads(NICHES_CONFIG.read_text())

    for entry in niches_data:
        existing = db.query(Niche).filter(Niche.slug == entry["slug"]).first()
        if existing:
            # Update subreddits from config if changed
            if set(existing.subreddits) != set(entry["subreddits"]):
                existing.subreddits = entry["subreddits"]
            continue

        niche = Niche(
            name=entry["name"],
            slug=entry["slug"],
            subreddits=entry["subreddits"],
            is_active=True,
        )
        db.add(niche)
        db.flush()

        schedule = ScheduleConfig(
            niche_id=niche.id,
            interval_minutes=60,
            is_enabled=False,
        )
        db.add(schedule)

    db.commit()

import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import Niche, ScheduleConfig

NICHES_CONFIG = Path(__file__).resolve().parent / "niches.json"

COLLECTION_DEFAULTS = {
    "now": 30,
    "daily": 1440,
    "weekly": 1440,
}


def _ensure_schedule_configs(db: Session, niche_id: int):
    existing = (
        db.query(ScheduleConfig.collection_type)
        .filter(ScheduleConfig.niche_id == niche_id)
        .all()
    )
    existing_types = {row[0] for row in existing}

    for ctype, interval in COLLECTION_DEFAULTS.items():
        if ctype not in existing_types:
            db.add(ScheduleConfig(
                niche_id=niche_id,
                collection_type=ctype,
                interval_minutes=interval,
                is_enabled=False,
            ))


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
            # Update description from config if changed
            new_desc = entry.get("description", "")
            if existing.description != new_desc:
                existing.description = new_desc
            # Ensure all 3 schedule configs exist
            _ensure_schedule_configs(db, existing.id)
            continue

        niche = Niche(
            name=entry["name"],
            slug=entry["slug"],
            subreddits=entry["subreddits"],
            description=entry.get("description", ""),
            is_active=True,
        )
        db.add(niche)
        db.flush()

        _ensure_schedule_configs(db, niche.id)

    db.commit()

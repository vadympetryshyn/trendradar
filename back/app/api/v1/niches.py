from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Niche
from app.schemas import ExternalNicheResponse

router = APIRouter(prefix="/niches", tags=["niches"])

COLLECTION_TYPES = [
    {"value": "now", "label": "Trends Now"},
    {"value": "rising", "label": "Rising Trends"},
    {"value": "daily", "label": "Trends Today"},
    {"value": "weekly", "label": "Trends This Week"},
]


@router.get("", response_model=list[ExternalNicheResponse])
def list_niches(db: Session = Depends(get_db)):
    return db.query(Niche).filter(Niche.is_active.is_(True)).order_by(Niche.sort_order).all()


@router.get("/collection-types")
def list_collection_types():
    return COLLECTION_TYPES

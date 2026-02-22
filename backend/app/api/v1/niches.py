from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Niche, Trend
from app.schemas import NicheDetailResponse, NicheResponse

router = APIRouter(prefix="/niches", tags=["niches"])


@router.get("", response_model=list[NicheResponse])
def list_niches(db: Session = Depends(get_db)):
    return db.query(Niche).filter(Niche.is_active.is_(True)).all()


@router.get("/{niche_id}", response_model=NicheDetailResponse)
def get_niche(niche_id: int, db: Session = Depends(get_db)):
    niche = db.query(Niche).filter(Niche.id == niche_id).first()
    if not niche:
        raise HTTPException(status_code=404, detail="Niche not found")

    active_count = (
        db.query(func.count(Trend.id))
        .filter(Trend.niche_id == niche_id, Trend.status == "active")
        .scalar()
    )
    expired_count = (
        db.query(func.count(Trend.id))
        .filter(Trend.niche_id == niche_id, Trend.status == "expired")
        .scalar()
    )

    return NicheDetailResponse(
        id=niche.id,
        name=niche.name,
        slug=niche.slug,
        subreddits=niche.subreddits,
        is_active=niche.is_active,
        created_at=niche.created_at,
        active_trend_count=active_count,
        expired_trend_count=expired_count,
    )

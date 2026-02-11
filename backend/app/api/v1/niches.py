from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Niche
from app.schemas import NicheResponse

router = APIRouter(prefix="/niches", tags=["niches"])


@router.get("", response_model=list[NicheResponse])
def list_niches(db: Session = Depends(get_db)):
    return db.query(Niche).filter(Niche.is_active.is_(True)).all()

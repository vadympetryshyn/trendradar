from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import TrendAnalysisResponse, PaginatedHistoryResponse, TrendAnalysisSummaryResponse
from app.services.trend_analysis_service import TrendAnalysisService

router = APIRouter(prefix="/trends", tags=["trends"])


@router.get("/{niche_slug}", response_model=TrendAnalysisResponse)
def get_latest_trends(niche_slug: str, db: Session = Depends(get_db)):
    service = TrendAnalysisService(db)
    analysis = service.get_latest_analysis(niche_slug)
    if not analysis:
        raise HTTPException(status_code=404, detail="No completed analysis found for this niche")
    return analysis


@router.get("/{niche_slug}/history", response_model=PaginatedHistoryResponse)
def get_analysis_history(
    niche_slug: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    service = TrendAnalysisService(db)
    items, total = service.get_analysis_history(niche_slug, page, per_page)
    return PaginatedHistoryResponse(
        items=[TrendAnalysisSummaryResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        per_page=per_page,
    )

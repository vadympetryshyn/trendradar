from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Niche, Trend
from app.schemas import (
    TrendDetail,
    TrendListItem,
    TrendListResponse,
    TrendSearchRequest,
    TrendSearchResponse,
    TrendSearchResult,
)
from app.services.embedding_service import EmbeddingService, get_embedding_service
from app.services.trend_collection_service import TrendCollectionService

router = APIRouter(prefix="/internal/trends", tags=["internal-trends"])


def _build_search_result(trend: Trend, distance: float) -> TrendSearchResult:
    similarity = round(1 - distance, 4)
    return TrendSearchResult(
        id=str(trend.id),
        title=trend.title,
        summary=trend.summary,
        source_post_ids=trend.source_post_ids or [],
        sentiment=trend.sentiment,
        category=trend.category,
        relevance_score=trend.relevance_score,
        collection_type=trend.collection_type,
        similarity=similarity,
        collected_at=trend.collected_at,
    )


@router.get("", response_model=TrendListResponse)
def list_trends(
    niche_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    collection_type: Optional[str] = Query(None),
    research_done: Optional[bool] = Query(None),
    has_embedding: Optional[bool] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(Trend)

    if status is not None:
        query = query.filter(Trend.status == status)
    else:
        query = query.filter(Trend.status == "active")

    if niche_id is not None:
        query = query.filter(Trend.niche_id == niche_id)

    if collection_type is not None:
        query = query.filter(Trend.collection_type == collection_type)

    if research_done is not None:
        query = query.filter(Trend.research_done.is_(research_done))

    if has_embedding is True:
        query = query.filter(Trend.embedding.isnot(None))
    elif has_embedding is False:
        query = query.filter(Trend.embedding.is_(None))

    total = query.count()
    trends = (
        query.order_by(Trend.relevance_score.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return TrendListResponse(
        items=[TrendListItem.model_validate(t) for t in trends],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/recommended", response_model=TrendSearchResponse)
def get_recommended(
    description: str = Query(..., min_length=3),
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
):
    query_embedding = embedding_service.generate_embedding(description)

    if query_embedding is None:
        raise HTTPException(status_code=503, detail="Embedding service unavailable")

    results = (
        db.query(
            Trend,
            Trend.embedding.cosine_distance(query_embedding).label("distance"),
        )
        .filter(Trend.status == "active", Trend.embedding.isnot(None))
        .order_by("distance")
        .limit(limit)
        .all()
    )

    return TrendSearchResponse(
        results=[_build_search_result(trend, distance) for trend, distance in results],
        query=description,
    )


@router.delete("/bulk")
def delete_trends_bulk(
    ids: List[str] = Body(..., embed=True),
    db: Session = Depends(get_db),
):
    deleted = db.query(Trend).filter(Trend.id.in_(ids)).delete(synchronize_session="fetch")
    if not deleted:
        raise HTTPException(status_code=404, detail="No trends found")

    db.commit()
    return {"detail": f"{deleted} trend(s) deleted"}


@router.get("/{trend_id}", response_model=TrendDetail)
def get_trend(trend_id: str, web_search: bool = Query(False), db: Session = Depends(get_db)):
    service = TrendCollectionService(db)
    trend = service.get_trend_by_id(trend_id, web_search=web_search)
    if not trend:
        raise HTTPException(status_code=404, detail="Trend not found")

    return TrendDetail.model_validate(trend)


@router.post("/search", response_model=TrendSearchResponse)
def search_trends(
    request: TrendSearchRequest,
    db: Session = Depends(get_db),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
):
    query_embedding = embedding_service.generate_embedding(request.query)

    if query_embedding is None:
        raise HTTPException(status_code=503, detail="Embedding service unavailable")

    query = db.query(
        Trend,
        Trend.embedding.cosine_distance(query_embedding).label("distance"),
    ).filter(Trend.embedding.isnot(None), Trend.status == "active")

    if request.niche is not None:
        niche = db.query(Niche).filter(Niche.slug == request.niche).first()
        if niche is not None:
            query = query.filter(Trend.niche_id == niche.id)

    results = query.order_by("distance").limit(request.limit).all()

    return TrendSearchResponse(
        results=[_build_search_result(trend, distance) for trend, distance in results],
        query=request.query,
    )

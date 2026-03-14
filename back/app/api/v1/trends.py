import random as random_module
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func

from app.database import get_db
from app.models import Trend
from app.config import settings
from app.schemas import (
    ExternalTrendDetail,
    ExternalTrendListItem,
    ExternalTrendListResponse,
    ExternalTrendSearchResponse,
    ExternalTrendSearchResult,
    TrendSearchRequest,
    VectorSearchRequest,
)
from app.services.embedding_service import EmbeddingService, get_embedding_service
from app.services.trend_collection_service import TrendCollectionService

router = APIRouter(prefix="/trends", tags=["trends"])


@router.get("", response_model=ExternalTrendListResponse)
def list_trends(
    niche_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    collection_type: Optional[str] = Query(None),
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

    total = query.count()
    trends = (
        query.order_by(Trend.relevance_score.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return ExternalTrendListResponse(
        items=[ExternalTrendListItem.model_validate(t) for t in trends],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/random", response_model=ExternalTrendListResponse)
def random_trends(
    collection_type: str = Query(..., description="Trend type: now, rising, daily, weekly"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(Trend).filter(
        Trend.status == "active",
        Trend.collection_type == collection_type,
    )

    total = query.count()
    trends = query.order_by(func.random()).offset(offset).limit(limit).all()

    return ExternalTrendListResponse(
        items=[ExternalTrendListItem.model_validate(t) for t in trends],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{trend_id}", response_model=ExternalTrendDetail)
def get_trend(trend_id: str, web_search: bool = Query(False), db: Session = Depends(get_db)):
    service = TrendCollectionService(db)
    trend = service.get_trend_by_id(trend_id, web_search=web_search)
    if not trend:
        raise HTTPException(status_code=404, detail="Trend not found")

    return ExternalTrendDetail.model_validate(trend)


@router.post("/search", response_model=ExternalTrendSearchResponse)
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

    if request.niche_id is not None:
        query = query.filter(Trend.niche_id == request.niche_id)

    results = query.order_by("distance").limit(request.limit).all()

    return ExternalTrendSearchResponse(
        results=[
            ExternalTrendSearchResult(
                id=str(trend.id),
                title=trend.title,
                summary=trend.summary,
                sentiment=trend.sentiment,
                category=trend.category,
                relevance_score=trend.relevance_score,
                collection_type=trend.collection_type,
                similarity=round(1 - distance, 4),
                collected_at=trend.collected_at,
            )
            for trend, distance in results
        ],
        query=request.query,
    )


@router.post("/search-by-vector", response_model=ExternalTrendSearchResponse)
def search_trends_by_vector(
    request: VectorSearchRequest,
    db: Session = Depends(get_db),
):
    expected_dim = settings.embedding_dimensions
    if len(request.embedding) != expected_dim:
        raise HTTPException(
            status_code=422,
            detail=f"Embedding must have {expected_dim} dimensions, got {len(request.embedding)}",
        )

    query = db.query(
        Trend,
        Trend.embedding.cosine_distance(request.embedding).label("distance"),
    ).filter(
        Trend.embedding.isnot(None),
        Trend.status == "active",
        Trend.collection_type.in_(request.collection_types),
    )

    if request.niche_id is not None:
        query = query.filter(Trend.niche_id == request.niche_id)

    fetch_limit = 10 if request.random else request.limit
    results = query.order_by("distance").limit(fetch_limit).all()

    if request.random:
        results = random_module.sample(results, min(request.random, len(results)))

    return ExternalTrendSearchResponse(
        results=[
            ExternalTrendSearchResult(
                id=str(trend.id),
                title=trend.title,
                summary=trend.summary,
                sentiment=trend.sentiment,
                category=trend.category,
                relevance_score=trend.relevance_score,
                collection_type=trend.collection_type,
                similarity=round(1 - distance, 4),
                collected_at=trend.collected_at,
            )
            for trend, distance in results
        ],
        query="vector_search",
    )

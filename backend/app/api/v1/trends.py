from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Trend
from app.schemas import (
    TrendDetail,
    TrendListItem,
    TrendListResponse,
    TrendSearchRequest,
    TrendSearchResponse,
    TrendSearchResult,
)
from app.services.embedding_service import EmbeddingService
from app.services.trend_collection_service import TrendCollectionService

router = APIRouter(prefix="/trends", tags=["trends"])


@router.get("", response_model=TrendListResponse)
def list_trends(
    niche_id: int | None = Query(None),
    trend_type: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(Trend).filter(Trend.status == "active")

    if niche_id is not None:
        query = query.filter(Trend.niche_id == niche_id)
    if trend_type is not None:
        query = query.filter(Trend.trend_type == trend_type)

    total = query.count()
    trends = (
        query.order_by(Trend.relevance_score.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    items = []
    for t in trends:
        items.append(TrendListItem(
            id=str(t.id),
            niche_id=t.niche_id,
            title=t.title,
            summary=t.summary,
            trend_type=t.trend_type,
            status=t.status,
            sentiment=t.sentiment,
            sentiment_score=t.sentiment_score,
            category=t.category,
            key_points=t.key_points,
            source_urls=t.source_urls,
            source_subreddits=t.source_subreddits,
            mention_count=t.mention_count,
            relevance_score=t.relevance_score,
            research_done=t.research_done,
            has_embedding=t.embedding is not None,
            collected_at=t.collected_at,
        ))

    return TrendListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/recommended", response_model=TrendSearchResponse)
def get_recommended(
    description: str = Query(..., min_length=3),
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    embedding_service = EmbeddingService()
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

    items = []
    for trend, distance in results:
        similarity = 1 - distance
        items.append(TrendSearchResult(
            id=str(trend.id),
            title=trend.title,
            summary=trend.summary,
            trend_type=trend.trend_type,
            sentiment=trend.sentiment,
            category=trend.category,
            relevance_score=trend.relevance_score,
            similarity=round(similarity, 4),
            collected_at=trend.collected_at,
        ))

    return TrendSearchResponse(results=items, query=description)


@router.delete("/bulk")
def delete_trends_bulk(
    ids: List[str] = Body(..., embed=True),
    db: Session = Depends(get_db),
):
    trends = db.query(Trend).filter(Trend.id.in_(ids)).all()
    if not trends:
        raise HTTPException(status_code=404, detail="No trends found")

    for trend in trends:
        db.delete(trend)

    db.commit()
    return {"detail": f"{len(trends)} trend(s) deleted"}


@router.get("/{trend_id}", response_model=TrendDetail)
def get_trend(trend_id: str, web_search: bool = Query(False), db: Session = Depends(get_db)):
    service = TrendCollectionService(db)
    trend = service.get_trend_by_id(trend_id, web_search=web_search)
    if not trend:
        raise HTTPException(status_code=404, detail="Trend not found")

    return TrendDetail(
        id=str(trend.id),
        niche_id=trend.niche_id,
        title=trend.title,
        summary=trend.summary,
        trend_type=trend.trend_type,
        status=trend.status,
        sentiment=trend.sentiment,
        sentiment_score=trend.sentiment_score,
        category=trend.category,
        key_points=trend.key_points,
        source_urls=trend.source_urls,
        source_subreddits=trend.source_subreddits,
        mention_count=trend.mention_count,
        relevance_score=trend.relevance_score,
        context_summary=trend.context_summary,
        research_citations=trend.research_citations or [],
        research_done=trend.research_done,
        has_embedding=trend.embedding is not None,
        researched_at=trend.researched_at,
        collected_at=trend.collected_at,
        expired_at=trend.expired_at,
    )


@router.post("/search", response_model=TrendSearchResponse)
def search_trends(
    request: TrendSearchRequest,
    db: Session = Depends(get_db),
):
    embedding_service = EmbeddingService()
    query_embedding = embedding_service.generate_embedding(request.query)

    if query_embedding is None:
        raise HTTPException(status_code=503, detail="Embedding service unavailable")

    query = db.query(
        Trend,
        Trend.embedding.cosine_distance(query_embedding).label("distance"),
    ).filter(Trend.embedding.isnot(None))

    if request.niche_id is not None:
        query = query.filter(Trend.niche_id == request.niche_id)

    results = query.order_by("distance").limit(request.limit).all()

    items = []
    for trend, distance in results:
        similarity = 1 - distance
        items.append(TrendSearchResult(
            id=str(trend.id),
            title=trend.title,
            summary=trend.summary,
            trend_type=trend.trend_type,
            sentiment=trend.sentiment,
            category=trend.category,
            relevance_score=trend.relevance_score,
            similarity=round(similarity, 4),
            collected_at=trend.collected_at,
        ))

    return TrendSearchResponse(results=items, query=request.query)

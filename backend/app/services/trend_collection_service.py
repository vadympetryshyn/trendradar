import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Niche, Trend
from app.services.embedding_service import EmbeddingService
from app.services.gemini_service import GeminiService
from app.services.perplexity_service import PerplexityService
from app.services.reddit_service import RedditService

logger = logging.getLogger(__name__)


class TrendCollectionService:
    def __init__(self, db: Session):
        self.db = db

    def collect_trends(self, niche_id: int) -> dict:
        niche = self.db.query(Niche).filter(Niche.id == niche_id).first()
        if not niche:
            raise ValueError(f"Niche with id {niche_id} not found")

        reddit = RedditService()
        gemini = GeminiService()
        embedding_service = EmbeddingService()

        try:
            all_posts = reddit.fetch_all_subreddits(niche.subreddits)

            if not all_posts:
                logger.warning(f"No posts fetched for niche {niche_id}")
                return {"created": 0, "expired": 0}

            result = gemini.analyze_posts(all_posts)

            post_url_map = {
                p["id"]: f"https://www.reddit.com{p['permalink']}"
                for p in all_posts
                if p.get("permalink")
            }

            # Delete previous active trends (replaced by new collection)
            expired_count = (
                self.db.query(Trend)
                .filter(Trend.niche_id == niche_id, Trend.status == "active")
                .delete()
            )
            self.db.flush()

            # Prepare new trends
            trends_data = result.get("trends", [])
            texts_for_embedding = []
            new_trends = []

            for trend_data in trends_data:
                source_post_ids = trend_data.get("source_post_ids", [])
                source_urls = [
                    post_url_map[pid]
                    for pid in source_post_ids
                    if pid in post_url_map
                ]

                trend = Trend(
                    niche_id=niche_id,
                    title=trend_data.get("title", ""),
                    summary=trend_data.get("summary", ""),
                    trend_type=trend_data.get("trend_type", "hot"),
                    status="active",
                    sentiment=trend_data.get("sentiment", "neutral"),
                    sentiment_score=float(trend_data.get("sentiment_score", 0.0)),
                    category=trend_data.get("category", "General"),
                    key_points=trend_data.get("key_points", []),
                    source_urls=source_urls,
                    source_subreddits=trend_data.get("source_subreddits", []),
                    mention_count=int(trend_data.get("mention_count", 0)),
                    relevance_score=float(trend_data.get("relevance_score", 0.0)),
                )
                new_trends.append(trend)
                texts_for_embedding.append(f"{trend.title} {trend.summary}")

            # Generate embeddings in batch
            embeddings = embedding_service.generate_embeddings(texts_for_embedding)

            for trend, emb in zip(new_trends, embeddings):
                trend.embedding = emb
                self.db.add(trend)

            self.db.commit()

            logger.info(
                f"Collection for niche {niche_id}: {len(new_trends)} created, {expired_count} expired"
            )
            return {"created": len(new_trends), "expired": expired_count}

        finally:
            reddit.close()
            gemini.close()

    def get_trend_by_id(self, trend_id, web_search: bool = False) -> Trend | None:
        trend = self.db.query(Trend).filter(Trend.id == trend_id).first()
        if not trend:
            return None

        if web_search and not trend.research_done:
            perplexity = PerplexityService()
            context, citations = perplexity.research_trend(trend.title, trend.summary)
            if context:
                trend.context_summary = context
                trend.research_citations = citations
                trend.research_done = True
                trend.researched_at = datetime.now(timezone.utc)

                # Regenerate embedding with context
                embedding_service = EmbeddingService()
                text = f"{trend.title} {trend.summary} {context}"
                embedding = embedding_service.generate_embedding(text)
                if embedding:
                    trend.embedding = embedding

                self.db.commit()
                self.db.refresh(trend)

        return trend

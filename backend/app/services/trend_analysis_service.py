import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session, joinedload

from app.models import Niche, TrendAnalysis, TrendItem
from app.services.gemini_service import GeminiService
from app.services.reddit_service import RedditService

logger = logging.getLogger(__name__)


class TrendAnalysisService:
    def __init__(self, db: Session):
        self.db = db

    def run_analysis(self, niche_id: int, celery_task_id: str | None = None) -> TrendAnalysis:
        niche = self.db.query(Niche).filter(Niche.id == niche_id).first()
        if not niche:
            raise ValueError(f"Niche with id {niche_id} not found")

        analysis = TrendAnalysis(niche_id=niche_id, status="pending", celery_task_id=celery_task_id)
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)

        reddit = RedditService()
        gemini = GeminiService()

        try:
            analysis.status = "fetching"
            self.db.commit()

            all_posts = reddit.fetch_all_subreddits(niche.subreddits)
            analysis.posts_fetched = len(all_posts)
            analysis.subreddits_fetched = len(
                set(p["subreddit"] for p in all_posts)
            )
            self.db.commit()

            if not all_posts:
                analysis.status = "failed"
                analysis.error_message = "No posts fetched from any subreddit"
                analysis.completed_at = datetime.now(timezone.utc)
                self.db.commit()
                return analysis

            analysis.status = "analyzing"
            self.db.commit()

            result = gemini.analyze_posts(all_posts)

            analysis.overall_summary = result.get("overall_summary", "")

            post_url_map = {
                p["id"]: f"https://www.reddit.com{p['permalink']}"
                for p in all_posts
                if p.get("permalink")
            }

            for trend_data in result.get("trends", []):
                source_post_ids = trend_data.get("source_post_ids", [])
                source_urls = [
                    post_url_map[pid]
                    for pid in source_post_ids
                    if pid in post_url_map
                ]

                item = TrendItem(
                    analysis_id=analysis.id,
                    title=trend_data.get("title", ""),
                    summary=trend_data.get("summary", ""),
                    sentiment=trend_data.get("sentiment", "neutral"),
                    sentiment_score=float(trend_data.get("sentiment_score", 0.0)),
                    category=trend_data.get("category", "General"),
                    key_points=trend_data.get("key_points", []),
                    source_urls=source_urls,
                    source_subreddits=trend_data.get("source_subreddits", []),
                    mention_count=int(trend_data.get("mention_count", 0)),
                    relevance_score=float(trend_data.get("relevance_score", 0.0)),
                )
                self.db.add(item)

            analysis.status = "completed"
            analysis.completed_at = datetime.now(timezone.utc)
            self.db.commit()

            logger.info(
                f"Analysis {analysis.id} completed: {len(result.get('trends', []))} trends found"
            )
            return analysis

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            analysis.status = "failed"
            analysis.error_message = str(e)
            analysis.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            raise

        finally:
            reddit.close()
            gemini.close()

    def get_latest_analysis(self, niche_slug: str) -> TrendAnalysis | None:
        return (
            self.db.query(TrendAnalysis)
            .join(Niche)
            .filter(Niche.slug == niche_slug, TrendAnalysis.status == "completed")
            .options(joinedload(TrendAnalysis.trend_items))
            .order_by(TrendAnalysis.completed_at.desc())
            .first()
        )

    def get_analysis_history(
        self, niche_slug: str, page: int = 1, per_page: int = 10
    ) -> tuple[list[TrendAnalysis], int]:
        query = (
            self.db.query(TrendAnalysis)
            .join(Niche)
            .filter(Niche.slug == niche_slug)
            .order_by(TrendAnalysis.started_at.desc())
        )
        total = query.count()
        items = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Niche, Trend
from app.services.embedding_service import get_embedding_service
from app.services.gemini_service import GeminiService
from app.services.perplexity_service import PerplexityService
from app.services.reddit_service import RedditService

logger = logging.getLogger(__name__)


def _percentile_rank(values: list[float], value: float) -> float:
    n = len(values)
    if n == 0:
        return 1.0
    count_below = sum(1 for v in values if v < value)
    count_equal = sum(1 for v in values if v == value)
    return (count_below + 0.5 * count_equal) / n


class TrendCollectionService:
    def __init__(self, db: Session):
        self.db = db

    def _compute_metrics(self, trends_data: list[dict], all_posts: list[dict]) -> list[dict]:
        post_map = {p["id"]: p for p in all_posts}

        # First pass: compute raw engagement for each trend
        trend_engagements = []
        trend_details = []

        for trend_data in trends_data:
            source_ids = trend_data.get("source_post_ids", [])
            valid_ids = [pid for pid in source_ids if pid in post_map]
            valid_posts = [post_map[pid] for pid in valid_ids]

            mention_count = len(valid_ids)

            total_score = sum(p.get("score", 0) for p in valid_posts)
            total_comments = sum(p.get("num_comments", 0) for p in valid_posts)
            engagement = total_score + total_comments

            trend_engagements.append(engagement)
            trend_details.append({
                "mention_count": mention_count,
                "engagement": engagement,
                "source_post_ids": valid_ids,
            })

        # Second pass: assign computed metrics
        enriched = []
        for i, trend_data in enumerate(trends_data):
            details = trend_details[i]

            # Relevance score = percentile rank of engagement
            relevance_score = round(_percentile_rank(trend_engagements, details["engagement"]), 4)

            enriched.append({
                "mention_count": details["mention_count"],
                "relevance_score": relevance_score,
                "source_post_ids": details["source_post_ids"],
            })

        return enriched

    def collect_trends(self, niche_id: int) -> dict:
        niche = self.db.query(Niche).filter(Niche.id == niche_id).first()
        if not niche:
            raise ValueError(f"Niche with id {niche_id} not found")

        logger.info(f"=== Starting trend collection for niche '{niche.name}' (id={niche_id}) ===")
        logger.info(f"Subreddits: {', '.join(niche.subreddits)}")

        reddit = RedditService()
        gemini = GeminiService()
        embedding_service = get_embedding_service()

        try:
            logger.info("Step 1/5: Scraping Reddit posts ...")
            all_posts = reddit.fetch_all_subreddits(niche.subreddits)

            if not all_posts:
                logger.warning(f"No posts fetched for niche {niche_id} — aborting collection")
                return {"created": 0, "expired": 0}

            logger.info(f"Step 2/5: Analyzing {len(all_posts)} posts with Gemini ...")
            result = gemini.analyze_posts(
                all_posts,
                niche_name=niche.name,
                niche_description=niche.description or "",
            )

            post_url_map = {
                p["id"]: f"https://www.reddit.com{p['permalink']}"
                for p in all_posts
                if p.get("permalink")
            }

            # Build post title map for enhanced embeddings
            post_title_map = {p["id"]: p.get("title", "") for p in all_posts}

            # Mark previous active trends as expired
            logger.info("Step 3/5: Expiring previous active trends ...")
            expired_count = (
                self.db.query(Trend)
                .filter(Trend.niche_id == niche_id, Trend.status == "active")
                .update(
                    {
                        Trend.status: "expired",
                        Trend.expired_at: datetime.now(timezone.utc),
                    }
                )
            )
            self.db.flush()
            logger.info(f"Expired {expired_count} previous trends")

            # Prepare new trends
            trends_data = result.get("trends", [])

            # Compute metrics from post data
            computed = self._compute_metrics(trends_data, all_posts)

            texts_for_embedding = []
            new_trends = []

            for trend_data, metrics in zip(trends_data, computed):
                source_post_ids = metrics["source_post_ids"]
                source_urls = [
                    post_url_map[pid]
                    for pid in source_post_ids
                    if pid in post_url_map
                ]

                trend = Trend(
                    niche_id=niche_id,
                    title=trend_data.get("title", ""),
                    summary=trend_data.get("summary", ""),
                    source_post_ids=source_post_ids,
                    status="active",
                    sentiment=trend_data.get("sentiment", "neutral"),
                    sentiment_score=float(trend_data.get("sentiment_score", 0.0)),
                    category=trend_data.get("category", "General"),
                    key_points=trend_data.get("key_points", []),
                    source_urls=source_urls,
                    source_subreddits=trend_data.get("source_subreddits", []),
                    mention_count=metrics["mention_count"],
                    relevance_score=metrics["relevance_score"],
                )
                new_trends.append(trend)

                # Enhanced embedding text with source post titles
                source_titles = " ".join(
                    post_title_map.get(pid, "") for pid in source_post_ids
                )
                texts_for_embedding.append(
                    f"{trend.title} {trend.summary} {source_titles}".strip()
                )

            logger.info(f"Step 4/5: Generating embeddings for {len(new_trends)} trends ...")
            # Generate embeddings in batch
            embeddings = embedding_service.generate_embeddings(texts_for_embedding)

            embedded_count = 0
            for trend, emb in zip(new_trends, embeddings):
                trend.embedding = emb
                if emb is not None:
                    embedded_count += 1
                self.db.add(trend)

            logger.info(f"Embeddings generated: {embedded_count}/{len(new_trends)} trends have embeddings")

            logger.info("Step 5/5: Saving trends to database ...")
            self.db.commit()

            logger.info(
                f"=== Collection complete for niche '{niche.name}': "
                f"{len(new_trends)} created, {expired_count} expired ==="
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
            logger.info(f"Researching trend '{trend.title}' via Perplexity ...")
            perplexity = PerplexityService()
            context, citations = perplexity.research_trend(trend.title, trend.summary)
            if context:
                logger.info(f"Perplexity returned {len(citations)} citations, updating trend ...")
                trend.context_summary = context
                trend.research_citations = citations
                trend.research_done = True
                trend.researched_at = datetime.now(timezone.utc)

                # Regenerate embedding with context
                logger.info("Regenerating embedding with research context ...")
                embedding_service = get_embedding_service()
                text = f"{trend.title} {trend.summary} {context}"
                embedding = embedding_service.generate_embedding(text)
                if embedding:
                    trend.embedding = embedding

                self.db.commit()
                self.db.refresh(trend)
                logger.info(f"Research complete for trend '{trend.title}'")

        return trend

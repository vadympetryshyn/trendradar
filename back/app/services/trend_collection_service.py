import logging
import math
import time
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Niche, Trend, SubredditStats
from app.services.embedding_service import get_embedding_service
from app.services.llm_service import LLMService
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
    # Baseline bounds for engagement normalization.
    # Floor prevents tiny subreddits from over-amplifying small signals.
    # Cap prevents large subreddits from suppressing genuinely popular posts.
    BASELINE_FLOOR_SCORE = 20
    BASELINE_FLOOR_COMMENTS = 10
    BASELINE_CAP_SCORE = 200
    BASELINE_CAP_COMMENTS = 80

    def __init__(self, db: Session):
        self.db = db

    def _compute_metrics(self, trends_data: list[dict], all_posts: list[dict]) -> list[dict]:
        post_map = {p["id"]: p for p in all_posts}

        # Load subreddit baselines for normalization
        stats_rows = self.db.query(SubredditStats).all()
        stats_map = {s.subreddit: s for s in stats_rows}

        # Fallback baseline from current batch (used when no per-subreddit stats exist)
        all_scores = [p["score"] for p in all_posts if p.get("score", 0) > 0]
        all_comments = [p["num_comments"] for p in all_posts if p.get("num_comments", 0) > 0]
        fallback_avg_score = sum(all_scores) / len(all_scores) if all_scores else 1.0
        fallback_avg_comments = sum(all_comments) / len(all_comments) if all_comments else 1.0

        # First pass: compute normalized engagement for each trend
        trend_engagements = []
        trend_details = []

        for trend_data in trends_data:
            source_ids = trend_data.get("source_post_ids", [])
            valid_ids = [pid for pid in source_ids if pid in post_map]
            valid_posts = [post_map[pid] for pid in valid_ids]

            mention_count = len(valid_ids)

            # Per-post normalized engagement with bounded baselines
            normalized_posts = []
            total_raw_engagement = 0
            for p in valid_posts:
                sub = p.get("subreddit", "")
                stats = stats_map.get(sub)
                score = p.get("score", 0)
                comments = p.get("num_comments", 0)

                total_raw_engagement += score + comments

                raw_base_score = stats.avg_score if stats and stats.avg_score > 0 else fallback_avg_score
                raw_base_comments = stats.avg_comments if stats and stats.avg_comments > 0 else fallback_avg_comments

                # Clamp baselines: floor prevents over-amplification from tiny subs,
                # cap prevents over-suppression from mega subs
                base_score = max(min(raw_base_score, self.BASELINE_CAP_SCORE), self.BASELINE_FLOOR_SCORE)
                base_comments = max(min(raw_base_comments, self.BASELINE_CAP_COMMENTS), self.BASELINE_FLOOR_COMMENTS)

                norm_score = score / base_score
                norm_comments = comments / base_comments
                normalized_posts.append(norm_score + norm_comments)

            # Weighted top-3 engagement: strong secondary posts contribute,
            # not just the single peak. This rewards trends with multiple
            # high-engagement posts (e.g. 7 posts about nano banana)
            # while keeping single-post trends unaffected (weight = 1.0 only).
            sorted_norms = sorted(normalized_posts, reverse=True)
            top_weights = [1.0, 0.5, 0.25]
            weighted_peak = sum(
                n * w for n, w in zip(sorted_norms, top_weights)
            ) if sorted_norms else 0.0

            # Cross-subreddit diversity boost
            unique_subs = len(set(p.get("subreddit", "") for p in valid_posts))
            cross_sub_boost = min((unique_subs - 1) * 0.2, 0.5)

            # Absolute engagement bonus using TOTAL raw engagement across
            # all posts — captures cumulative volume, not just the best post.
            # Single-post trends: total = max (no change).
            # Multi-post trends: naturally boosted by combined volume.
            absolute_bonus = math.log2(total_raw_engagement + 1) * 0.1 if total_raw_engagement > 0 else 0.0

            engagement = weighted_peak + cross_sub_boost + absolute_bonus

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

    def _save_trends(
        self,
        trends_data: list[dict],
        all_posts: list[dict],
        niche_id: int,
        collection_type: str,
    ) -> list[Trend]:
        post_url_map = {
            p["id"]: f"https://www.reddit.com{p['permalink']}"
            for p in all_posts
            if p.get("permalink")
        }
        # External article URLs from link posts (not Reddit permalinks)
        post_external_url_map = {
            p["id"]: p["url"]
            for p in all_posts
            if p.get("url")
        }
        post_title_map = {p["id"]: p.get("title", "") for p in all_posts}

        computed = self._compute_metrics(trends_data, all_posts)

        texts_for_embedding = []
        new_trends = []

        for trend_data, metrics in zip(trends_data, computed):
            source_post_ids = metrics["source_post_ids"]
            # Reddit discussion permalinks
            mention_urls = [
                post_url_map[pid]
                for pid in source_post_ids
                if pid in post_url_map
            ]
            # External article URLs
            source_urls = [
                post_external_url_map[pid]
                for pid in source_post_ids
                if pid in post_external_url_map
            ]

            trend = Trend(
                niche_id=niche_id,
                title=trend_data.get("title", ""),
                summary=trend_data.get("summary", ""),
                source_post_ids=source_post_ids,
                status="active",
                sentiment=trend_data.get("sentiment", "neutral"),
                category=trend_data.get("category", "General"),
                key_points=trend_data.get("key_points", []),
                source_urls=source_urls,
                mention_urls=mention_urls,
                source_subreddits=trend_data.get("source_subreddits", []),
                mention_count=metrics["mention_count"],
                relevance_score=metrics["relevance_score"],
                collection_type=collection_type,
            )
            new_trends.append(trend)

            source_titles = " ".join(
                post_title_map.get(pid, "") for pid in source_post_ids
            )
            texts_for_embedding.append(
                f"{trend.title} {trend.summary} {source_titles}".strip()
            )

        # Generate embeddings in batch
        embedding_service = get_embedding_service()
        embeddings = embedding_service.generate_embeddings(texts_for_embedding)

        embedded_count = 0
        for trend, emb in zip(new_trends, embeddings):
            trend.embedding = emb
            if emb is not None:
                embedded_count += 1
            self.db.add(trend)

        logger.info(f"Embeddings generated: {embedded_count}/{len(new_trends)} trends have embeddings")
        return new_trends

    def _compute_baselines(self, hot_posts: list[dict]) -> dict[str, dict]:
        by_sub: dict[str, list[dict]] = {}
        now = time.time()
        for p in hot_posts:
            sub = p.get("subreddit", "")
            if sub:
                by_sub.setdefault(sub, []).append(p)

        baselines = {}
        for sub, posts in by_sub.items():
            scores = []
            comments = []
            ages = []
            velocities = []
            for p in posts:
                score = p.get("score", 0)
                num_comments = p.get("num_comments", 0)
                age_hours = max((now - p.get("created_utc", now)) / 3600, 0.01)
                velocity = (score + num_comments) / age_hours
                scores.append(score)
                comments.append(num_comments)
                ages.append(age_hours)
                velocities.append(velocity)

            n = len(posts)
            baselines[sub] = {
                "avg_score": sum(scores) / n,
                "avg_comments": sum(comments) / n,
                "avg_age_hours": sum(ages) / n,
                "avg_velocity": sum(velocities) / n,
                "post_count": n,
            }
        return baselines

    def _upsert_baselines(self, baselines: dict[str, dict]) -> None:
        for sub, stats in baselines.items():
            existing = (
                self.db.query(SubredditStats)
                .filter(SubredditStats.subreddit == sub)
                .first()
            )
            if existing:
                existing.avg_score = stats["avg_score"]
                existing.avg_comments = stats["avg_comments"]
                existing.avg_age_hours = stats["avg_age_hours"]
                existing.avg_velocity = stats["avg_velocity"]
                existing.post_count = stats["post_count"]
                existing.updated_at = datetime.now(timezone.utc)
            else:
                self.db.add(SubredditStats(
                    subreddit=sub,
                    avg_score=stats["avg_score"],
                    avg_comments=stats["avg_comments"],
                    avg_age_hours=stats["avg_age_hours"],
                    avg_velocity=stats["avg_velocity"],
                    post_count=stats["post_count"],
                    updated_at=datetime.now(timezone.utc),
                ))
        self.db.flush()

    def _filter_new_posts(self, new_posts: list[dict], baselines: dict[str, dict]) -> list[dict]:
        now = time.time()
        filtered = []
        skip_age_young = 0
        skip_age_old = 0
        skip_low_score = 0
        skip_no_baseline = 0
        skip_low_velocity = 0

        for p in new_posts:
            age_hours = (now - p.get("created_utc", now)) / 3600
            # Skip posts younger than 5 min or older than 3 hours
            if age_hours < 5 / 60:
                skip_age_young += 1
                continue
            if age_hours > 3:
                skip_age_old += 1
                continue
            score = p.get("score", 0)
            if score < 20:
                skip_low_score += 1
                continue

            num_comments = p.get("num_comments", 0)
            velocity = (score + num_comments) / max(age_hours, 0.01)

            sub = p.get("subreddit", "")
            baseline = baselines.get(sub)
            if not baseline or baseline["avg_velocity"] <= 0:
                skip_no_baseline += 1
                continue

            velocity_ratio = velocity / baseline["avg_velocity"]
            if velocity_ratio < 0.3:
                skip_low_velocity += 1
                continue

            p["velocity"] = velocity
            p["velocity_ratio"] = velocity_ratio
            filtered.append(p)

        logger.info(
            f"Rising filter breakdown: {len(new_posts)} total -> "
            f"skip_age_young={skip_age_young}, skip_age_old={skip_age_old}, "
            f"skip_low_score={skip_low_score}, skip_no_baseline={skip_no_baseline}, "
            f"skip_low_velocity={skip_low_velocity}, passed={len(filtered)}"
        )
        if filtered:
            for p in filtered[:5]:
                logger.info(
                    f"  Passed: r/{p.get('subreddit')} [{p['id']}] "
                    f"score={p.get('score')}, comments={p.get('num_comments')}, "
                    f"velocity={p['velocity']:.1f}, ratio={p['velocity_ratio']:.2f}x — {p.get('title', '')[:80]}"
                )

        filtered.sort(key=lambda x: x.get("velocity_ratio", 0), reverse=True)
        return filtered

    def _annotate_engagement_ratios(self, posts: list[dict]) -> None:
        """Annotate posts with engagement_ratio vs subreddit baseline (from SubredditStats)."""
        stats_rows = self.db.query(SubredditStats).all()
        stats_map = {s.subreddit: s for s in stats_rows}
        if not stats_map:
            return

        for p in posts:
            sub = p.get("subreddit", "")
            stats = stats_map.get(sub)
            if not stats or stats.avg_score <= 0:
                continue
            baseline = stats.avg_score + (stats.avg_comments or 0)
            if baseline > 0:
                ratio = (p.get("score", 0) + p.get("num_comments", 0)) / baseline
                p["engagement_ratio"] = round(ratio, 1)

    def collect_rising_trends(self, niche_id: int) -> dict:
        niche = self.db.query(Niche).filter(Niche.id == niche_id).first()
        if not niche:
            raise ValueError(f"Niche with id {niche_id} not found")

        logger.info(f"=== Starting rising trend detection for niche '{niche.name}' (id={niche_id}) ===")

        # Load baselines from SubredditStats (saved by the preceding "now" collection)
        stats_rows = (
            self.db.query(SubredditStats)
            .filter(SubredditStats.subreddit.in_(niche.subreddits))
            .all()
        )
        baselines = {
            s.subreddit: {
                "avg_score": s.avg_score,
                "avg_comments": s.avg_comments,
                "avg_age_hours": s.avg_age_hours,
                "avg_velocity": s.avg_velocity,
                "post_count": s.post_count,
            }
            for s in stats_rows
            if s.avg_velocity and s.avg_velocity > 0
        }

        if not baselines:
            logger.info("Rising detection: no baselines in DB, skipping")
            expired = self._expire_trends(niche_id, "rising")
            self.db.commit()
            return {"created": 0, "expired": expired}

        logger.info(f"Rising detection: loaded baselines for {len(baselines)} subreddits")

        reddit = RedditService()
        llm = LLMService()
        try:
            all_new_posts: list[dict] = []
            for sub in niche.subreddits:
                if sub not in baselines:
                    logger.info(f"Rising detection: skipping r/{sub} (no baseline)")
                    continue
                try:
                    new_posts = reddit.fetch_subreddit_new(sub)
                    all_new_posts.extend(new_posts)
                    logger.info(f"Rising detection: fetched {len(new_posts)} /new posts from r/{sub}")
                except Exception as e:
                    logger.warning(f"Rising detection: failed to fetch /new for r/{sub}: {e}")

            filtered = self._filter_new_posts(all_new_posts, baselines)
            logger.info(f"Rising detection: {len(filtered)} posts passed filter (from {len(all_new_posts)} total)")

            expired_count = self._expire_trends(niche_id, "rising")
            logger.info(f"Rising detection: expired {expired_count} previous rising trends")

            if not filtered:
                logger.info("Rising detection: no posts passed filter, skipping Gemini call")
                self.db.commit()
                return {"created": 0, "expired": expired_count}

            logger.info(f"Rising detection: analyzing {len(filtered)} posts with Gemini ...")
            result = llm.analyze_posts(
                filtered,
                niche_name=niche.name,
                niche_description=niche.description or "",
                collection_type="rising",
            )
            trends_data = result.get("trends", [])

            if not trends_data:
                logger.info("Rising detection: Gemini returned no rising trends")
                self.db.commit()
                return {"created": 0, "expired": expired_count}

            new_trends = self._save_trends(trends_data, filtered, niche_id, "rising")
            self.db.commit()

            logger.info(
                f"=== Rising detection complete for niche '{niche.name}': "
                f"{len(new_trends)} created, {expired_count} expired ==="
            )
            return {"created": len(new_trends), "expired": expired_count}
        finally:
            reddit.close()
            llm.close()

    def _expire_trends(self, niche_id: int, collection_type: str) -> int:
        expired_count = (
            self.db.query(Trend)
            .filter(
                Trend.niche_id == niche_id,
                Trend.status == "active",
                Trend.collection_type == collection_type,
            )
            .update(
                {
                    Trend.status: "expired",
                    Trend.expired_at: datetime.now(timezone.utc),
                }
            )
        )
        self.db.flush()
        return expired_count

    def collect_trends(self, niche_id: int, collection_type: str = "now") -> dict:
        if collection_type == "rising":
            raise ValueError("'rising' cannot be triggered manually — it runs automatically within 'now' collections")

        niche = self.db.query(Niche).filter(Niche.id == niche_id).first()
        if not niche:
            raise ValueError(f"Niche with id {niche_id} not found")

        logger.info(
            f"=== Starting trend collection for niche '{niche.name}' "
            f"(id={niche_id}, collection_type={collection_type}) ==="
        )
        logger.info(f"Subreddits: {', '.join(niche.subreddits)}")

        reddit = RedditService()
        llm = LLMService()

        try:
            logger.info("Step 1: Scraping Reddit posts ...")
            all_posts = reddit.fetch_all_subreddits(niche.subreddits, collection_type)

            if not all_posts:
                logger.warning(f"No posts fetched for niche {niche_id} — aborting collection")
                return {"created": 0, "expired": 0}

            # Annotate posts with engagement ratio vs subreddit baselines
            if collection_type == "now":
                self._annotate_engagement_ratios(all_posts)

            logger.info(f"Step 2: Analyzing {len(all_posts)} posts with Gemini ({collection_type}) ...")
            result = llm.analyze_posts(
                all_posts,
                niche_name=niche.name,
                niche_description=niche.description or "",
                collection_type=collection_type,
            )
            trends_data = result.get("trends", [])

            # Expire previous active trends scoped to this collection type
            logger.info(f"Step 3: Expiring previous '{collection_type}' active trends ...")
            expired_count = self._expire_trends(niche.id, collection_type)
            logger.info(f"Expired {expired_count} previous trends")

            # Save trends
            logger.info("Step 4: Saving trends and generating embeddings ...")
            new_trends = self._save_trends(trends_data, all_posts, niche.id, collection_type)

            # For "now" collections, update subreddit baselines so the separate
            # rising detection task can use them without re-fetching hot posts.
            if collection_type == "now":
                logger.info("Step 4b: Updating subreddit baselines ...")
                baselines = self._compute_baselines(all_posts)
                if baselines:
                    self._upsert_baselines(baselines)
                    logger.info(f"Baselines updated for {len(baselines)} subreddits")

            logger.info("Step 5: Committing to database ...")
            self.db.commit()

            logger.info(
                f"=== Collection complete for niche '{niche.name}' ({collection_type}): "
                f"{len(new_trends)} created, {expired_count} expired ==="
            )
            return {
                "created": len(new_trends),
                "expired": expired_count,
            }

        finally:
            reddit.close()
            llm.close()

    def get_trend_by_id(self, trend_id, web_search: bool = False) -> Trend | None:
        trend = self.db.query(Trend).filter(Trend.id == trend_id).first()
        if not trend:
            return None

        if web_search and not trend.research_done:
            logger.info(f"Researching trend '{trend.title}' via Exa AI ...")
            perplexity = PerplexityService()
            context, citations = perplexity.research_trend(
                trend.title, trend.summary, trend.key_points
            )
            if context:
                logger.info(f"Exa AI returned {len(citations)} citations, updating trend ...")
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

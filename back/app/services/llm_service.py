import hashlib
import json
import logging
import time

import httpx
import redis

from app.config import settings

logger = logging.getLogger(__name__)

# Cache TTL per collection type
_LLM_CACHE_TTL = {
    "now": 3 * 60 * 60,      # 3 hours (covers 2h interval with margin)
    "daily": 7 * 60 * 60,    # 7 hours (covers 6h interval)
    "weekly": 25 * 60 * 60,  # 25 hours (covers 24h interval)
}

# Minimum overlap ratio to consider a cached result reusable
_FUZZY_MATCH_THRESHOLD = 0.9  # 90% of post IDs must match


class LLMService:
    def __init__(self):
        self.client = httpx.Client(timeout=120.0)
        self.api_key = settings.google_api_key
        self._redis = redis.Redis.from_url(settings.redis_url, decode_responses=True)

    def _select_posts(self, posts: list[dict]) -> list[dict]:
        # Force-include breakout posts (engagement_ratio >= 3x their subreddit average)
        # so small-sub hot content isn't drowned out by large-sub volume.
        breakout = [p for p in posts if p.get("engagement_ratio", 0) >= 3.0]
        breakout_ids = {p["id"] for p in breakout}

        rest = [p for p in posts if p["id"] not in breakout_ids]
        rest.sort(key=lambda p: p.get("score", 0) + p.get("num_comments", 0), reverse=True)

        # Breakout posts first (sorted by engagement_ratio), then the rest
        breakout.sort(key=lambda p: p.get("engagement_ratio", 0), reverse=True)
        return breakout + rest

    def _build_prompt(
        self,
        posts: list[dict],
        niche_name: str = "",
        niche_description: str = "",
        collection_type: str = "now",
    ) -> str:
        niche_context = ""
        if niche_name:
            niche_context = f"You are analyzing trends in the {niche_name} niche"
            if niche_description:
                niche_context += f": {niche_description}"
            niche_context += "\n\n"

        if collection_type == "now":
            prompt = self._build_now_prompt(posts, niche_context)
        elif collection_type == "daily":
            prompt = self._build_daily_prompt(posts, niche_context)
        elif collection_type == "weekly":
            prompt = self._build_weekly_prompt(posts, niche_context)
        else:
            prompt = self._build_now_prompt(posts, niche_context)

        return prompt

    def _build_now_prompt(self, posts: list[dict], niche_context: str) -> str:
        prompt = f"""{niche_context}You are an expert trend analyst. Analyze the following hot Reddit posts and identify the most significant current trends.

CRITICAL RULES:
- Each trend MUST focus on ONE specific topic, event, product, or development. Don't combine multiple unrelated news items into a single trend.
- Some posts include an "engagement_ratio" (e.g. 3.2x) showing how many times more engagement they have compared to their subreddit's average. Posts with high engagement_ratio are breakout content — pay special attention to these and make sure they appear as trends even if only one post covers the topic.
- source_post_ids MUST only contain post IDs that are genuinely about the trend topic. Do NOT include unrelated posts — carefully verify each post's title and content actually matches the trend before adding its ID. A wrong source_post_id corrupts the trend data.

For each trend, provide:
- title: A concise, specific title for the trend (name the specific product/event/topic)
- summary: A 2-5 sentence description of what this trend is about
- sentiment: One of "positive", "negative", "neutral", or "mixed"
- category: A category like "Research", "Product Launch", "Open Source", "Ethics", "Industry", "Tutorial", "Discussion", "Regulation", etc.
- key_points: An array of 2-5 key points about this trend
- source_subreddits: An array of subreddit names where this trend appeared
- source_post_ids: An array of post IDs (the "id" field shown in brackets) that are related to this trend — only include posts that are actually about this specific trend

Identify between 5 and 15 trends, ordered by significance (highest first).

Return JSON in this exact format:
{{
  "trends": [
    {{
      "title": "string",
      "summary": "string",
      "sentiment": "string",
      "category": "string",
      "key_points": ["string"],
      "source_subreddits": ["string"],
      "source_post_ids": ["string"]
    }}
  ]
}}

Here are the Reddit posts to analyze:

"""
        prompt += self._format_posts(posts)
        return prompt

    def _build_daily_prompt(self, posts: list[dict], niche_context: str) -> str:
        prompt = f"""{niche_context}You are an expert trend analyst. Analyze the top Reddit posts from the past day and identify the most significant trends.

CRITICAL RULES:
- Each trend MUST focus on ONE specific topic, event, product, or development. NEVER combine multiple unrelated news items into a single trend.
- For example, if there are posts about "Qwen 3.5 release" and "Liquid AI new model", these MUST be separate trends — do NOT merge them into "New Model Releases" or similar umbrella trends.
- Only group posts together if they are genuinely about the SAME specific thing (e.g. multiple posts discussing Qwen 3.5 specifically).
- Prefer more specific trends over fewer generic ones.
- source_post_ids MUST only contain post IDs that are genuinely about the trend topic. Do NOT include unrelated posts — carefully verify each post's title and content actually matches the trend before adding its ID. A wrong source_post_id corrupts the trend data.

For each trend, provide:
- title: A concise, specific title for the trend (name the specific product/event/topic)
- summary: A 2-5 sentence description of what this trend is about
- sentiment: One of "positive", "negative", "neutral", or "mixed"
- category: A category like "Research", "Product Launch", "Open Source", "Ethics", "Industry", "Tutorial", "Discussion", "Regulation", etc.
- key_points: An array of 2-5 key points about this trend
- source_subreddits: An array of subreddit names where this trend appeared
- source_post_ids: An array of post IDs (the "id" field shown in brackets) that are related to this trend — only include posts that are actually about this specific trend

Identify between 5 and 15 trends, ordered by significance (highest first).

Return JSON in this exact format:
{{
  "trends": [
    {{
      "title": "string",
      "summary": "string",
      "sentiment": "string",
      "category": "string",
      "key_points": ["string"],
      "source_subreddits": ["string"],
      "source_post_ids": ["string"]
    }}
  ]
}}

Here are the top Reddit posts from the past day:

"""
        prompt += self._format_posts(posts)
        return prompt

    def _build_weekly_prompt(self, posts: list[dict], niche_context: str) -> str:
        prompt = f"""{niche_context}You are an expert trend analyst. Analyze the top Reddit posts from the past week and identify the most significant trends.

CRITICAL RULES:
- Each trend MUST focus on ONE specific topic, event, product, or development. NEVER combine multiple unrelated news items into a single trend.
- For example, if there are posts about "Qwen 3.5 release" and "Liquid AI new model", these MUST be separate trends — do NOT merge them into "New Model Releases" or similar umbrella trends.
- Only group posts together if they are genuinely about the SAME specific thing (e.g. multiple posts discussing Qwen 3.5 specifically).
- Prefer more specific trends over fewer generic ones.
- source_post_ids MUST only contain post IDs that are genuinely about the trend topic. Do NOT include unrelated posts — carefully verify each post's title and content actually matches the trend before adding its ID. A wrong source_post_id corrupts the trend data.

For each trend, provide:
- title: A concise, specific title for the trend (name the specific product/event/topic)
- summary: A 2-5 sentence description of what this trend is about
- sentiment: One of "positive", "negative", "neutral", or "mixed"
- category: A category like "Research", "Product Launch", "Open Source", "Ethics", "Industry", "Tutorial", "Discussion", "Regulation", etc.
- key_points: An array of 2-5 key points about this trend
- source_subreddits: An array of subreddit names where this trend appeared
- source_post_ids: An array of post IDs (the "id" field shown in brackets) that are related to this trend — only include posts that are actually about this specific trend

Identify between 15 and 30 trends, ordered by significance (highest first).

Return JSON in this exact format:
{{
  "trends": [
    {{
      "title": "string",
      "summary": "string",
      "sentiment": "string",
      "category": "string",
      "key_points": ["string"],
      "source_subreddits": ["string"],
      "source_post_ids": ["string"]
    }}
  ]
}}

Here are the top Reddit posts from the past week:

"""
        prompt += self._format_posts(posts)
        return prompt

    def _format_posts(self, posts: list[dict]) -> str:
        text = ""
        now = time.time()
        for p in posts:
            age_hours = (now - p.get("created_utc", now)) / 3600
            stats = f"score: {p['score']}, comments: {p['num_comments']}, age: {age_hours:.1f}h"
            if p.get("engagement_ratio"):
                stats += f", engagement_ratio: {p['engagement_ratio']}x"
            posts_text = (
                f"[id:{p['id']}] [r/{p['subreddit']}] ({stats})\n"
                f"Title: {p['title']}\n"
            )
            if p.get("selftext"):
                posts_text += f"Text: {p['selftext'][:500]}\n"
            posts_text += "\n"
            text += posts_text
        return text

    def _cache_index_key(self, niche_name: str, collection_type: str) -> str:
        """Redis set key that tracks all cache entries for a niche+type."""
        slug = niche_name.lower().replace(" ", "-").replace("&", "")
        return f"llm:index:{slug}:{collection_type}"

    def _find_fuzzy_match(self, post_ids: set[str], niche_name: str, collection_type: str) -> tuple[dict | None, float]:
        """Scan cached entries for this niche+type and return the best fuzzy match."""
        index_key = self._cache_index_key(niche_name, collection_type)
        cache_keys = self._redis.smembers(index_key)

        best_match = None
        best_overlap = 0.0

        for ck in cache_keys:
            data = self._redis.get(ck)
            if not data:
                # Expired entry — clean up index
                self._redis.srem(index_key, ck)
                continue
            try:
                entry = json.loads(data)
            except json.JSONDecodeError:
                self._redis.srem(index_key, ck)
                continue

            cached_ids = set(entry.get("_post_ids", []))
            if not cached_ids:
                continue

            # Jaccard-style overlap: intersection / union
            overlap = len(post_ids & cached_ids) / len(post_ids | cached_ids)
            if overlap > best_overlap:
                best_overlap = overlap
                best_match = entry

        return best_match, best_overlap

    def _store_cache_entry(self, post_ids: list[str], result: dict, niche_name: str, collection_type: str) -> None:
        """Store LLM result with post IDs for fuzzy matching."""
        content = f"{niche_name}:{collection_type}:" + ",".join(sorted(post_ids))
        digest = hashlib.sha256(content.encode()).hexdigest()[:16]
        cache_key = f"llm:cache:{digest}"

        ttl = _LLM_CACHE_TTL.get(collection_type, 3 * 60 * 60)
        entry = {**result, "_post_ids": post_ids}
        self._redis.setex(cache_key, ttl, json.dumps(entry))

        # Add to index set (with same TTL so it auto-expires)
        index_key = self._cache_index_key(niche_name, collection_type)
        self._redis.sadd(index_key, cache_key)
        self._redis.expire(index_key, ttl)

    def analyze_posts(
        self,
        posts: list[dict],
        niche_name: str = "",
        niche_description: str = "",
        collection_type: str = "now",
    ) -> dict:
        selected = self._select_posts(posts)
        breakout_count = sum(1 for p in selected if p.get("engagement_ratio", 0) >= 3.0)
        logger.info(
            f"Selected {len(selected)} posts for LLM analysis "
            f"(from {len(posts)} total, collection={collection_type}, "
            f"breakout_posts={breakout_count})"
        )

        # Check LLM result cache — fuzzy match on post IDs (90%+ overlap = hit)
        post_ids = [p["id"] for p in selected]
        post_id_set = set(post_ids)
        logger.info(
            f"LLM cache check: niche={niche_name}, type={collection_type}, posts={len(post_ids)}"
        )
        cached, overlap = self._find_fuzzy_match(post_id_set, niche_name, collection_type)
        if cached and overlap >= _FUZZY_MATCH_THRESHOLD:
            # Check if any NEW posts are breakout-level — if so, force reanalysis
            cached_ids = set(cached.get("_post_ids", []))
            new_post_ids = post_id_set - cached_ids
            force_reanalyze = False
            if new_post_ids:
                new_posts = [p for p in selected if p["id"] in new_post_ids]
                breakout_new = [p for p in new_posts if p.get("engagement_ratio", 0) >= 3.0]
                if breakout_new:
                    force_reanalyze = True
                    titles = [p.get("title", "?")[:60] for p in breakout_new]
                    logger.info(
                        f"LLM CACHE OVERRIDE: {len(breakout_new)} breakout post(s) among "
                        f"{len(new_post_ids)} new posts — forcing reanalysis. "
                        f"Breakout titles: {titles}"
                    )

            if not force_reanalyze:
                cached.pop("_post_ids", None)
                trend_count = len(cached.get("trends", []))
                logger.info(
                    f"LLM CACHE HIT (fuzzy): {trend_count} cached trends returned, "
                    f"overlap={overlap:.1%}, threshold={_FUZZY_MATCH_THRESHOLD:.0%} — skipped API call"
                )
                return cached

        if cached and overlap >= _FUZZY_MATCH_THRESHOLD:
            # Fell through from breakout override
            pass
        elif cached:
            logger.info(
                f"LLM CACHE MISS: best overlap={overlap:.1%}, "
                f"below threshold={_FUZZY_MATCH_THRESHOLD:.0%} — calling OpenRouter"
            )
        else:
            logger.info("LLM CACHE MISS: no cached entries found — calling OpenRouter")

        prompt = self._build_prompt(selected, niche_name, niche_description, collection_type)

        # Primary: OpenRouter
        if settings.openrouter_api_key:
            from app.services.openrouter_service import OpenRouterService
            logger.info("Sending posts to OpenRouter for trend analysis ...")
            openrouter = OpenRouterService()
            try:
                result = openrouter.call(prompt)
                trend_count = len(result.get("trends", []))
                logger.info(f"OpenRouter analysis complete: {trend_count} trends identified")
                self._store_cache_entry(post_ids, result, niche_name, collection_type)
                ttl = _LLM_CACHE_TTL.get(collection_type, 3 * 60 * 60)
                logger.info(f"LLM CACHE SET: stored {trend_count} trends, TTL={ttl}s")
                return result
            except Exception as e:
                logger.error(f"OpenRouter failed: {e}")
            finally:
                openrouter.close()

        logger.error("No LLM provider returned a result — returning empty trends")
        return {"trends": []}

    def close(self):
        self.client.close()

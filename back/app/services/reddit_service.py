import json
import logging
import random
import time

import httpx
import redis

from app.config import settings

logger = logging.getLogger(__name__)

USER_AGENT = "TrendRadar/1.0 (trend analysis bot)"

# Cache TTL per collection type (seconds)
_CACHE_TTL = {
    "now": 10 * 60,       # 10 min — hot posts change frequently
    "daily": 30 * 60,     # 30 min
    "weekly": 60 * 60,    # 1 hour
    "new": 5 * 60,        # 5 min — rising detection
}


class ProxyTrafficExhausted(Exception):
    """Raised when the residential proxy quota is depleted."""


class RedditService:
    def __init__(self):
        client_kwargs = {
            "headers": {"User-Agent": USER_AGENT},
            "timeout": 30.0,
            "follow_redirects": True,
        }

        if settings.dataimpulse_proxy:
            client_kwargs["proxy"] = settings.dataimpulse_proxy
            logger.info("Reddit service using residential proxy")
        else:
            logger.info("Reddit service using direct connection (no proxy)")

        self.client = httpx.Client(**client_kwargs)
        self._redis = redis.Redis.from_url(settings.redis_url, decode_responses=True)

    def _cache_key(self, subreddit: str, endpoint_type: str) -> str:
        return f"reddit:cache:{subreddit.lower()}:{endpoint_type}"

    def _get_cached(self, subreddit: str, endpoint_type: str) -> list[dict] | None:
        key = self._cache_key(subreddit, endpoint_type)
        data = self._redis.get(key)
        if data:
            logger.info(f"Cache hit for r/{subreddit} ({endpoint_type})")
            return json.loads(data)
        return None

    def _set_cache(self, subreddit: str, endpoint_type: str, posts: list[dict]) -> None:
        key = self._cache_key(subreddit, endpoint_type)
        ttl = _CACHE_TTL.get(endpoint_type, 10 * 60)
        self._redis.setex(key, ttl, json.dumps(posts))

    def _fetch_with_retry(self, url: str, max_retries: int = 3) -> httpx.Response:
        for attempt in range(max_retries):
            try:
                response = self.client.get(url)

                # Proxy quota exhausted — abort immediately, no retries
                if response.status_code == 407 or "TRAFFIC_EXHAUSTED" in response.text[:200]:
                    raise ProxyTrafficExhausted(
                        "Residential proxy traffic exhausted — top up your DataImpulse account"
                    )

                # Reddit returned HTML instead of JSON — blocked, don't retry
                content_type = response.headers.get("content-type", "")
                if response.status_code == 403 and "html" in content_type:
                    logger.warning(f"Reddit returned 403 HTML for {url} — blocked, skipping")
                    raise httpx.HTTPStatusError(
                        "403 blocked (HTML response)", request=response.request, response=response
                    )

                if response.status_code == 429 or response.status_code >= 500:
                    wait = (2 ** attempt) + random.random() + 3
                    logger.warning(
                        f"Reddit returned {response.status_code} for {url}, "
                        f"retrying in {wait:.1f}s (attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(wait)
                    continue
                response.raise_for_status()
                return response
            except (ProxyTrafficExhausted, httpx.HTTPStatusError):
                raise
            except Exception as e:
                # Catch proxy errors (407 comes as ProxyError, not HTTP response)
                if "TRAFFIC_EXHAUSTED" in str(e):
                    raise ProxyTrafficExhausted(
                        "Residential proxy traffic exhausted — top up your DataImpulse account"
                    )
                if attempt < max_retries - 1:
                    wait = (2 ** attempt) + random.random() + 3
                    logger.warning(f"Request failed for {url}: {e}, retrying in {wait:.1f}s")
                    time.sleep(wait)
                else:
                    raise
        # Final attempt without retry
        response = self.client.get(url)
        response.raise_for_status()
        return response

    def _fetch_endpoints(self, subreddit: str, endpoints: list[str], endpoint_type: str = "now") -> list[dict]:
        # Check cache first
        cached = self._get_cached(subreddit, endpoint_type)
        if cached is not None:
            return cached

        seen_ids = set()
        posts = []

        for url in endpoints:
            try:
                logger.info(f"Scraping r/{subreddit} ...")
                time.sleep(random.uniform(4, 7))
                response = self._fetch_with_retry(url)
                data = response.json()

                for child in data.get("data", {}).get("children", []):
                    post = child.get("data", {})
                    post_id = post.get("id")
                    if not post_id or post_id in seen_ids:
                        continue
                    if post.get("stickied", False):
                        continue
                    seen_ids.add(post_id)

                    selftext = post.get("selftext", "") or ""
                    if len(selftext) > 2000:
                        selftext = selftext[:2000].rsplit(" ", 1)[0]

                    # Capture external URL for link posts (not self posts)
                    external_url = post.get("url", "")
                    if external_url and post.get("is_self", False):
                        external_url = ""

                    posts.append({
                        "id": post_id,
                        "title": post.get("title", ""),
                        "selftext": selftext,
                        "score": post.get("score", 0),
                        "num_comments": post.get("num_comments", 0),
                        "subreddit": post.get("subreddit", subreddit),
                        "permalink": post.get("permalink", ""),
                        "url": external_url,
                        "created_utc": post.get("created_utc", 0),
                    })
            except ProxyTrafficExhausted:
                raise
            except Exception as e:
                logger.warning(f"Failed to fetch {url}: {e}")
                continue

        logger.info(f"Scraped r/{subreddit}: {len(posts)} unique posts collected")

        # Cache even empty results to avoid re-fetching blocked subreddits
        self._set_cache(subreddit, endpoint_type, posts)
        return posts

    def fetch_subreddit_now(self, subreddit: str) -> list[dict]:
        endpoints = [
            f"https://www.reddit.com/r/{subreddit}/hot.json?limit=20",
        ]
        return self._fetch_endpoints(subreddit, endpoints, "now")

    def fetch_subreddit_new(self, subreddit: str) -> list[dict]:
        endpoints = [f"https://www.reddit.com/r/{subreddit}/new.json?limit=30"]
        return self._fetch_endpoints(subreddit, endpoints, "new")

    def fetch_subreddit_daily(self, subreddit: str) -> list[dict]:
        endpoints = [
            f"https://www.reddit.com/r/{subreddit}/top.json?t=day&limit=30",
        ]
        return self._fetch_endpoints(subreddit, endpoints, "daily")

    def fetch_subreddit_weekly(self, subreddit: str) -> list[dict]:
        endpoints = [
            f"https://www.reddit.com/r/{subreddit}/top.json?t=week&limit=30",
        ]
        return self._fetch_endpoints(subreddit, endpoints, "weekly")

    def fetch_subreddit_posts(self, subreddit: str) -> list[dict]:
        """Legacy method — same as fetch_subreddit_now."""
        return self.fetch_subreddit_now(subreddit)

    def fetch_all_subreddits(self, subreddits: list[str], collection_type: str = "now") -> list[dict]:
        all_posts = []
        fetched_subreddits = []

        logger.info(
            f"Starting Reddit scraping ({collection_type}) for "
            f"{len(subreddits)} subreddits: {', '.join(subreddits)}"
        )

        fetch_method = {
            "now": self.fetch_subreddit_now,
            "daily": self.fetch_subreddit_daily,
            "weekly": self.fetch_subreddit_weekly,
        }.get(collection_type, self.fetch_subreddit_now)

        for subreddit in subreddits:
            try:
                posts = fetch_method(subreddit)
                if posts:
                    all_posts.extend(posts)
                    fetched_subreddits.append(subreddit)
                    logger.info(f"Fetched {len(posts)} posts from r/{subreddit}")
            except ProxyTrafficExhausted:
                logger.error(
                    f"Proxy traffic exhausted after fetching {len(fetched_subreddits)} subreddits — "
                    f"aborting remaining {len(subreddits) - subreddits.index(subreddit)} subreddits"
                )
                break
            except Exception as e:
                logger.warning(f"Skipping r/{subreddit}: {e}")
                continue

        logger.info(f"Reddit scraping complete: {len(all_posts)} total posts from {len(fetched_subreddits)} subreddits")
        return all_posts

    def close(self):
        self.client.close()

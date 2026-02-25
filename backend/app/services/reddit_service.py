import logging
import random
import time

import httpx

logger = logging.getLogger(__name__)

USER_AGENT = "TrendsRadar/1.0 (trend analysis bot)"


class RedditService:
    def __init__(self):
        self.client = httpx.Client(
            headers={"User-Agent": USER_AGENT},
            timeout=30.0,
            follow_redirects=True,
        )

    def _fetch_with_retry(self, url: str, max_retries: int = 3) -> httpx.Response:
        for attempt in range(max_retries):
            try:
                response = self.client.get(url)
                if response.status_code in (403, 429) or response.status_code >= 500:
                    wait = (2 ** attempt) + random.random()
                    logger.warning(
                        f"Reddit returned {response.status_code} for {url}, "
                        f"retrying in {wait:.1f}s (attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(wait)
                    continue
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError:
                raise
            except Exception as e:
                if attempt < max_retries - 1:
                    wait = (2 ** attempt) + random.random()
                    logger.warning(f"Request failed for {url}: {e}, retrying in {wait:.1f}s")
                    time.sleep(wait)
                else:
                    raise
        # Final attempt without retry
        response = self.client.get(url)
        response.raise_for_status()
        return response

    def _fetch_endpoints(self, subreddit: str, endpoints: list[str]) -> list[dict]:
        seen_ids = set()
        posts = []

        for url in endpoints:
            try:
                logger.info(f"Scraping r/{subreddit} ...")
                time.sleep(2)
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

                    posts.append({
                        "id": post_id,
                        "title": post.get("title", ""),
                        "selftext": selftext,
                        "score": post.get("score", 0),
                        "num_comments": post.get("num_comments", 0),
                        "subreddit": post.get("subreddit", subreddit),
                        "permalink": post.get("permalink", ""),
                        "created_utc": post.get("created_utc", 0),
                    })
            except Exception as e:
                logger.warning(f"Failed to fetch {url}: {e}")
                continue

        logger.info(f"Scraped r/{subreddit}: {len(posts)} unique posts collected")
        return posts

    def fetch_subreddit_now(self, subreddit: str) -> list[dict]:
        endpoints = [
            f"https://www.reddit.com/r/{subreddit}/hot.json?limit=20",
        ]
        return self._fetch_endpoints(subreddit, endpoints)

    def fetch_subreddit_new(self, subreddit: str) -> list[dict]:
        endpoints = [f"https://www.reddit.com/r/{subreddit}/new.json?limit=30"]
        return self._fetch_endpoints(subreddit, endpoints)

    def fetch_subreddit_daily(self, subreddit: str) -> list[dict]:
        endpoints = [
            f"https://www.reddit.com/r/{subreddit}/top.json?t=day&limit=25",
        ]
        return self._fetch_endpoints(subreddit, endpoints)

    def fetch_subreddit_weekly(self, subreddit: str) -> list[dict]:
        endpoints = [
            f"https://www.reddit.com/r/{subreddit}/top.json?t=week&limit=30",
        ]
        return self._fetch_endpoints(subreddit, endpoints)

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
            except Exception as e:
                logger.warning(f"Skipping r/{subreddit}: {e}")
                continue

        logger.info(f"Reddit scraping complete: {len(all_posts)} total posts from {len(fetched_subreddits)} subreddits")
        return all_posts

    def close(self):
        self.client.close()

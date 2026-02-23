import logging
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

    def fetch_subreddit_posts(self, subreddit: str) -> list[dict]:
        endpoints = [
            (f"https://www.reddit.com/r/{subreddit}/hot.json?limit=25", "hot"),
            (f"https://www.reddit.com/r/{subreddit}/rising.json?limit=10", "rising"),
        ]

        seen_ids = set()
        posts = []

        for url, trend_type in endpoints:
            try:
                time.sleep(2)
                response = self.client.get(url)
                response.raise_for_status()
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
                        selftext = selftext[:2000]

                    posts.append({
                        "id": post_id,
                        "title": post.get("title", ""),
                        "selftext": selftext,
                        "score": post.get("score", 0),
                        "num_comments": post.get("num_comments", 0),
                        "subreddit": post.get("subreddit", subreddit),
                        "permalink": post.get("permalink", ""),
                        "trend_type": trend_type,
                    })
            except Exception as e:
                logger.warning(f"Failed to fetch {url}: {e}")
                continue

        return posts

    def fetch_all_subreddits(self, subreddits: list[str]) -> list[dict]:
        all_posts = []
        fetched_subreddits = []

        for subreddit in subreddits:
            try:
                posts = self.fetch_subreddit_posts(subreddit)
                if posts:
                    all_posts.extend(posts)
                    fetched_subreddits.append(subreddit)
                    logger.info(f"Fetched {len(posts)} posts from r/{subreddit}")
            except Exception as e:
                logger.warning(f"Skipping r/{subreddit}: {e}")
                continue

        return all_posts

    def close(self):
        self.client.close()

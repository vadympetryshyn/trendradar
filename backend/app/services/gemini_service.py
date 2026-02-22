import json
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

GEMINI_MODEL = "gemini-3-flash-preview"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

ANALYSIS_PROMPT = """You are an expert trend analyst. Analyze the following Reddit posts and identify the most significant trends.

Each post includes a [type:hot] or [type:rising] tag indicating whether it came from a hot or rising endpoint. Use this to classify each trend:
- "hot" = trend is well-established and widely discussed
- "rising" = trend is emerging and gaining traction

For each trend, provide:
- title: A concise title for the trend
- summary: A 2-3 sentence description of what this trend is about
- trend_type: Either "hot" or "rising" based on the majority of source posts
- sentiment: One of "positive", "negative", "neutral", or "mixed"
- sentiment_score: A float from -1.0 (very negative) to 1.0 (very positive)
- category: A category like "Research", "Product Launch", "Open Source", "Ethics", "Industry", "Tutorial", "Discussion", "Regulation", etc.
- key_points: An array of 2-4 key points about this trend
- source_subreddits: An array of subreddit names where this trend appeared
- source_post_ids: An array of post IDs (the "id" field shown in brackets) that are related to this trend
- mention_count: Estimated number of posts related to this trend
- relevance_score: A float from 0.0 to 1.0 indicating how significant this trend is

Identify between 5 and 15 trends, ordered by relevance_score (highest first).

Return JSON in this exact format:
{
  "trends": [
    {
      "title": "string",
      "summary": "string",
      "trend_type": "hot",
      "sentiment": "string",
      "sentiment_score": 0.0,
      "category": "string",
      "key_points": ["string"],
      "source_subreddits": ["string"],
      "source_post_ids": ["string"],
      "mention_count": 0,
      "relevance_score": 0.0
    }
  ]
}

Here are the Reddit posts to analyze:

"""


class GeminiService:
    def __init__(self):
        self.client = httpx.Client(timeout=120.0)
        self.api_key = settings.google_api_key

    def analyze_posts(self, posts: list[dict]) -> dict:
        sorted_posts = sorted(posts, key=lambda p: p.get("score", 0), reverse=True)[:100]

        posts_text = ""
        for p in sorted_posts:
            trend_type = p.get("trend_type", "hot")
            posts_text += f"[id:{p['id']}] [type:{trend_type}] [r/{p['subreddit']}] (score: {p['score']}, comments: {p['num_comments']})\n"
            posts_text += f"Title: {p['title']}\n"
            if p.get("selftext"):
                posts_text += f"Text: {p['selftext'][:500]}\n"
            posts_text += "\n"

        prompt = ANALYSIS_PROMPT + posts_text

        for attempt in range(2):
            try:
                response = self.client.post(
                    GEMINI_URL,
                    params={"key": self.api_key},
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {
                            "temperature": 0.3,
                            "responseMimeType": "application/json",
                        },
                    },
                )
                response.raise_for_status()
                result = response.json()

                text = result["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(text)

                if "trends" not in parsed:
                    raise ValueError("Missing 'trends' key in response")

                return parsed

            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.warning(f"Gemini parse attempt {attempt + 1} failed: {e}")
                if attempt == 0:
                    continue
                raise
            except httpx.HTTPStatusError as e:
                logger.error(f"Gemini API error: {e.response.status_code} - {e.response.text}")
                raise

    def close(self):
        self.client.close()

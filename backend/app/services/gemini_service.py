import json
import logging
import time

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

GEMINI_MODEL = "gemini-3-flash-preview"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"


class GeminiService:
    def __init__(self):
        self.client = httpx.Client(timeout=120.0)
        self.api_key = settings.google_api_key

    def _select_posts(self, posts: list[dict]) -> list[dict]:
        guaranteed = []
        hot = []
        guaranteed_ids: set[str] = set()

        for p in posts:
            trend_type = p.get("trend_type")
            if trend_type in ("rising", "top"):
                guaranteed.append(p)
                guaranteed_ids.add(p["id"])
            else:
                hot.append(p)

        hot.sort(key=lambda p: p.get("score", 0), reverse=True)

        budget = 200 - len(guaranteed)
        hot_fill = [p for p in hot if p["id"] not in guaranteed_ids][:max(0, budget)]

        selected = guaranteed + hot_fill
        return selected[:200]

    def _build_prompt(self, posts: list[dict], niche_name: str = "", niche_description: str = "") -> str:
        niche_context = ""
        if niche_name:
            niche_context = f"You are analyzing trends in the {niche_name} niche"
            if niche_description:
                niche_context += f": {niche_description}"
            niche_context += "\n\n"

        prompt = f"""{niche_context}You are an expert trend analyst. Analyze the following Reddit posts and identify the most significant trends.

Each post includes a [type:hot], [type:rising], or [type:top] tag indicating its source endpoint.

For each trend, provide:
- title: A concise title for the trend
- summary: A 2-5 sentence description of what this trend is about
- sentiment: One of "positive", "negative", "neutral", or "mixed"
- category: A category like "Research", "Product Launch", "Open Source", "Ethics", "Industry", "Tutorial", "Discussion", "Regulation", etc.
- key_points: An array of 2-5 key points about this trend
- source_subreddits: An array of subreddit names where this trend appeared
- source_post_ids: An array of post IDs (the "id" field shown in brackets) that are related to this trend

Identify between 5 and 20 trends, ordered by significance (highest first).

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

        now = time.time()
        for p in posts:
            trend_type = p.get("trend_type", "hot")
            age_hours = (now - p.get("created_utc", now)) / 3600
            posts_text = (
                f"[id:{p['id']}] [type:{trend_type}] [r/{p['subreddit']}] "
                f"(score: {p['score']}, comments: {p['num_comments']}, age: {age_hours:.1f}h)\n"
                f"Title: {p['title']}\n"
            )
            if p.get("selftext"):
                posts_text += f"Text: {p['selftext'][:500]}\n"
            posts_text += "\n"
            prompt += posts_text

        return prompt

    def _call_gemini(self, prompt: str) -> dict:
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

    def analyze_posts(self, posts: list[dict], niche_name: str = "", niche_description: str = "") -> dict:
        selected = self._select_posts(posts)
        logger.info(f"Selected {len(selected)} posts for Gemini analysis (from {len(posts)} total)")
        prompt = self._build_prompt(selected, niche_name, niche_description)

        try:
            logger.info(f"Sending posts to Gemini ({GEMINI_MODEL}) for trend analysis ...")
            result = self._call_gemini(prompt)
            trend_count = len(result.get("trends", []))
            logger.info(f"Gemini analysis complete: {trend_count} trends identified")
            return result
        except Exception as e:
            logger.error(f"Gemini failed: {e}, trying OpenRouter fallback...")
            # Try OpenRouter fallback
            if settings.openrouter_api_key:
                from app.services.openrouter_service import OpenRouterService
                logger.info("Falling back to OpenRouter ...")
                openrouter = OpenRouterService()
                try:
                    result = openrouter.call(prompt)
                    trend_count = len(result.get("trends", []))
                    logger.info(f"OpenRouter fallback complete: {trend_count} trends identified")
                    return result
                finally:
                    openrouter.close()
            raise

    def close(self):
        self.client.close()

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

PERPLEXITY_URL = "https://api.perplexity.ai/chat/completions"

RESEARCH_PROMPT = """You are a research assistant. Given the following trend title and summary from Reddit discussions, provide a comprehensive factual context.

Include:
1. Factual explanation of what this trend is about
2. Key numbers, statistics, or data points if available
3. Notable quotes or statements from key figures
4. Why this trend matters and its potential impact
5. Brief timeline of recent developments

Keep your response concise (under 3000 characters). Focus on facts, not opinions.

Trend Title: {title}
Trend Summary: {summary}"""


class PerplexityService:
    def __init__(self):
        self.api_key = settings.perplexity_api_key

    def research_trend(self, title: str, summary: str) -> str | None:
        if not self.api_key:
            logger.warning("Perplexity API key not configured, skipping research")
            return None

        try:
            prompt = RESEARCH_PROMPT.format(title=title, summary=summary)

            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    PERPLEXITY_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "sonar",
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 1024,
                    },
                )
                response.raise_for_status()
                result = response.json()

                content = result["choices"][0]["message"]["content"]
                return content[:3000]

        except Exception as e:
            logger.error(f"Perplexity research failed for '{title}': {e}")
            return None

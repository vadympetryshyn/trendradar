import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

PERPLEXITY_URL = "https://api.perplexity.ai/chat/completions"

RESEARCH_SYSTEM_PROMPT = """You are a research assistant providing factual context about trending topics.

When responding, cover these aspects:
1. What specifically happened (the event/announcement/development)
2. Key numbers, statistics, or data points
3. Notable quotes or statements from key figures
4. Background context about the subject matter
5. Why this matters and its potential impact
6. Brief timeline of recent developments

Keep your response concise (under 3000 characters). Focus on facts, not opinions.
Always prioritize the specific event or development, not just general background."""

RESEARCH_QUERY = """{title}. {summary}{source_urls_section}"""


class PerplexityService:
    def __init__(self):
        self.api_key = settings.perplexity_api_key

    def research_trend(
        self,
        title: str,
        summary: str,
        key_points: list[str] | None = None,
        source_urls: list[str] | None = None,
    ) -> tuple[str | None, list[str]]:
        """Returns (content, citations) tuple."""
        if not self.api_key:
            logger.warning("Perplexity API key not configured, skipping research")
            return None, []

        try:
            source_urls_section = ""
            if source_urls:
                external_urls = [u for u in source_urls if "reddit.com" not in u]
                if external_urls:
                    source_urls_section = " Source: " + external_urls[0]

            query = RESEARCH_QUERY.format(
                title=title,
                summary=summary,
                source_urls_section=source_urls_section,
            )

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
                            {"role": "system", "content": RESEARCH_SYSTEM_PROMPT},
                            {"role": "user", "content": query},
                        ],
                        "max_tokens": 1024,
                    },
                )
                response.raise_for_status()
                result = response.json()

                content = result["choices"][0]["message"]["content"]
                citations = result.get("citations", [])
                return content[:3000], citations

        except Exception as e:
            logger.error(f"Perplexity research failed for '{title}': {e}")
            return None, []

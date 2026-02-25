import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

PERPLEXITY_URL = "https://api.perplexity.ai/chat/completions"

RESEARCH_PROMPT = """You are a research assistant. Given the following trend from Reddit discussions, provide comprehensive factual context.

IMPORTANT: Your research must cover TWO aspects:
1. **The specific event/topic** described in the trend (e.g. if the trend is about a model being released on a website, research that specific event — when it happened, what was announced, community reaction)
2. **Background context** about the subject matter (e.g. if it's about a new AI model, include its specs, capabilities, benchmarks, how it compares to competitors)

Do NOT only research the general subject — always prioritize the specific event or development that the trend is about.

Include:
1. What specifically happened (the event/announcement/development)
2. Key numbers, statistics, or data points
3. Notable quotes or statements from key figures
4. Background context about the subject matter
5. Why this matters and its potential impact
6. Brief timeline of recent developments

Keep your response concise (under 3000 characters). Focus on facts, not opinions.

Trend Title: {title}
Trend Summary: {summary}
{key_points_section}"""


class PerplexityService:
    def __init__(self):
        self.api_key = settings.perplexity_api_key

    def research_trend(self, title: str, summary: str, key_points: list[str] | None = None) -> tuple[str | None, list[str]]:
        """Returns (content, citations) tuple."""
        if not self.api_key:
            logger.warning("Perplexity API key not configured, skipping research")
            return None, []

        try:
            key_points_section = ""
            if key_points:
                points_text = "\n".join(f"- {p}" for p in key_points)
                key_points_section = f"Key Points:\n{points_text}"

            prompt = RESEARCH_PROMPT.format(title=title, summary=summary, key_points_section=key_points_section)

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
                citations = result.get("citations", [])
                return content[:3000], citations

        except Exception as e:
            logger.error(f"Perplexity research failed for '{title}': {e}")
            return None, []

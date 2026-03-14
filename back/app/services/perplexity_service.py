import logging

from exa_py import Exa

from app.config import settings

logger = logging.getLogger(__name__)

RESEARCH_QUERY = """{title}. {summary}"""


class PerplexityService:
    """Web research service using Exa AI (formerly used Perplexity)."""

    def __init__(self):
        self.api_key = settings.exa_ai_api_key

    def research_trend(
        self,
        title: str,
        summary: str,
        key_points: list[str] | None = None,
    ) -> tuple[str | None, list[str]]:
        """Returns (content, citations) tuple."""
        if not self.api_key:
            logger.warning("Exa AI API key not configured, skipping research")
            return None, []

        try:
            query = RESEARCH_QUERY.format(
                title=title,
                summary=summary,
            )

            exa = Exa(api_key=self.api_key)
            results = exa.search_and_contents(
                query=query,
                num_results=5,
                summary={"query": query},
                type="auto",
            )

            citations = []
            content_parts = []
            for r in results.results:
                citations.append(r.url)
                result_summary = getattr(r, "summary", None) or ""
                content_parts.append(f"**{r.title}**\n{r.url}\n{result_summary}")

            content = "\n\n---\n\n".join(content_parts)

            return content[:3000], citations

        except Exception as e:
            logger.error(f"Exa AI research failed for '{title}': {e}")
            return None, []

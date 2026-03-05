import json
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "google/gemini-3.0-flash"


class OpenRouterService:
    def __init__(self):
        self.client = httpx.Client(timeout=120.0)
        self.api_key = settings.openrouter_api_key

    def call(self, prompt: str) -> dict:
        for attempt in range(2):
            try:
                response = self.client.post(
                    OPENROUTER_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": OPENROUTER_MODEL,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.3,
                        "response_format": {"type": "json_object"},
                    },
                )
                response.raise_for_status()
                result = response.json()

                text = result["choices"][0]["message"]["content"]
                parsed = json.loads(text)

                if "trends" not in parsed:
                    raise ValueError("Missing 'trends' key in OpenRouter response")

                logger.info("OpenRouter fallback succeeded")
                return parsed

            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.warning(f"OpenRouter parse attempt {attempt + 1} failed: {e}")
                if attempt == 0:
                    continue
                raise
            except httpx.HTTPStatusError as e:
                logger.error(f"OpenRouter API error: {e.response.status_code} - {e.response.text}")
                raise

    def close(self):
        self.client.close()

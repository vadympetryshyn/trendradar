import logging

from openai import OpenAI

from app.config import settings

logger = logging.getLogger(__name__)

_instance: "EmbeddingService | None" = None


class EmbeddingService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
        self.model = "text-embedding-3-small"

    def generate_embedding(self, text: str) -> list[float] | None:
        if not self.client:
            logger.warning("OpenAI API key not configured, skipping embedding")
            return None
        try:
            response = self.client.embeddings.create(
                input=text,
                model=self.model,
                dimensions=settings.embedding_dimensions,
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None

    def generate_embeddings(self, texts: list[str]) -> list[list[float] | None]:
        if not self.client:
            logger.warning("OpenAI API key not configured, skipping embeddings")
            return [None] * len(texts)
        try:
            logger.info(f"Generating embeddings for {len(texts)} texts (model={self.model}, dims={settings.embedding_dimensions}) ...")
            response = self.client.embeddings.create(
                input=texts,
                model=self.model,
                dimensions=settings.embedding_dimensions,
            )
            result: list[list[float] | None] = [None] * len(texts)
            for item in response.data:
                result[item.index] = item.embedding
            logger.info(f"Embeddings generated successfully for {len(texts)} texts")
            return result
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            return [None] * len(texts)


def get_embedding_service() -> EmbeddingService:
    global _instance
    if _instance is None:
        _instance = EmbeddingService()
    return _instance

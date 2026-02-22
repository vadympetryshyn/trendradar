from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://trendsradar:trendsradar@postgres:5432/trendsradar"
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/1"
    app_env: str = "development"
    google_api_key: str = ""
    perplexity_api_key: str = ""
    openai_api_key: str = ""
    embedding_dimensions: int = 1536

    model_config = {
        "env_file": ".env",
    }


settings = Settings()

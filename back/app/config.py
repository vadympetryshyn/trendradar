from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://trendradar:trendradar@postgres:5432/trendradar"
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/1"
    app_env: str = "development"
    google_api_key: str = ""
    exa_ai_api_key: str = ""
    openai_api_key: str = ""
    xai_api_key: str = ""
    openrouter_api_key: str = ""
    embedding_dimensions: int = 1536
    dataimpulse_proxy: str = ""

    # Security / JWT
    jwt_secret_key: str = "change-this-in-production-to-a-secure-random-string"
    jwt_algorithm: str = "HS256"
    access_token_expire_days: int = 30

    # Email (FastAPI-Mail)
    mail_username: Optional[str] = None
    mail_password: Optional[str] = None
    mail_from: Optional[str] = None
    mail_port: int = 587
    mail_server: str = "smtp.gmail.com"
    mail_from_name: str = "TrendRadar"
    mail_starttls: bool = True
    mail_ssl_tls: bool = False
    mail_use_credentials: bool = True
    support_email: str = "support@postory.io"

    # Registration gate
    registration_enabled: bool = False

    # Frontend URL for email links
    frontend_url: str = "http://localhost:3000"

    # CORS allowed origins (comma-separated)
    allowed_origins: str = "http://localhost:3005,http://localhost:5550,http://localhost:5551"

    # Google OAuth
    google_oauth_client_id: Optional[str] = None

    model_config = {
        "env_file": ".env",
    }


settings = Settings()

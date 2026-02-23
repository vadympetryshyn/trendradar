from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.database import Base, SessionLocal, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()

    Base.metadata.create_all(bind=engine)

    # Add new columns to existing tables
    with engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE trends ADD COLUMN IF NOT EXISTS research_citations VARCHAR[] DEFAULT '{}'
        """))
        conn.commit()

    db = SessionLocal()
    try:
        from app.seed import seed_data

        seed_data(db)
    finally:
        db.close()

    yield


app = FastAPI(title="TrendsRadar API", lifespan=lifespan)

if settings.app_env == "development":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

from app.api.v1.router import api_v1_router  # noqa: E402

app.include_router(api_v1_router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "trendsradar-api"}

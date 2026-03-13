# TrendRadar — Claude Project Guide

## Project Overview

TrendRadar is a trend tracking and analysis platform with AI-powered vector search capabilities. It consists of a Next.js frontend, a FastAPI backend, async task processing via Celery, and vector embeddings via pgvector.

---

## Repository Structure

```
trendradar/
├── front/                    # Next.js frontend
├── back/                     # FastAPI backend
├── docker-compose.yml        # Development environment
├── docker-compose.prod.yml   # Production environment
├── nginx.conf                # Nginx reverse proxy config
├── DEPLOY.md                 # Deployment instructions
└── API_README.md             # API documentation
```

---

## Tech Stack

### Frontend
- **Next.js 16** (App Router) + **React 19** + **TypeScript 5**
- **Tailwind CSS 4** + shadcn/ui + Radix UI
- **React Hook Form** + **Zod** for form validation
- Google OAuth via `@react-oauth/google`

### Backend
- **Python 3.12** + **FastAPI 0.115** + **Uvicorn**
- **SQLAlchemy 2.0** ORM + **Alembic** migrations
- **Celery 5.4** (async tasks) + **Redis 7** (broker/cache)
- **OpenAI** integration + **pgvector** for vector embeddings
- **python-jose** (JWT auth) + **fastapi-mail** (email)

### Infrastructure
- **PostgreSQL 16** with `pgvector` extension
- **Redis 7** (Celery broker + caching)
- **Nginx** reverse proxy

---

## Docker Services

### Development (`docker-compose.yml`)

| Service        | Image                  | Port (host→container) | Notes                        |
|---------------|------------------------|----------------------|------------------------------|
| `front`        | node:20-alpine         | 3005→3000            | Next.js dev server           |
| `back`         | python:3.12-slim       | 3006→8000            | FastAPI with `--reload`      |
| `celery`       | (same as back)         | —                    | Worker, concurrency=2        |
| `celery-beat`  | (same as back)         | —                    | Scheduled/cron tasks         |
| `db`           | pgvector/pgvector:pg16 | 5433→5432            | Postgres with vector support |
| `redis`        | redis:7-alpine         | 6379→6379            | Broker + cache               |

All services use health checks and dependency ordering. Code is mounted as volumes for live reload.

### Production (`docker-compose.prod.yml`)

- Builds from `Dockerfile.prod` (optimized, no dev tools)
- Celery worker: autoscale 1–10 concurrency
- No host port exposure for internal services
- Uses `.env.production` for secrets

---

## Environment Variables

**Backend** — loaded from `back/.env`:
```
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://redis:6379
SECRET_KEY=...
OPENAI_API_KEY=...
```

**Frontend** — loaded from `front/.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:3006
```

---

## Development Workflow

```bash
# Start full stack (dev)
docker compose up

# Rebuild a specific service
docker compose up --build back

# Run migrations
docker compose exec back alembic upgrade head

# Open a shell
docker compose exec back bash
docker compose exec front sh
```

---

## Key Architecture Notes

- All async I/O: FastAPI uses `async/await` throughout; SQLAlchemy async sessions.
- Vector search: embeddings stored in Postgres via pgvector; queried with cosine similarity.
- Task queue: Celery workers consume from Redis; Beat scheduler handles periodic jobs.
- Auth: JWT tokens issued by backend; Google OAuth supported on frontend.
- Nginx routes `/api/*` to backend (`3006`) and everything else to frontend (`3005`) in dev; in prod handles SSL termination.

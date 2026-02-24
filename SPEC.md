# TrendsRadar — Technical Specification

## Overview

TrendsRadar is a standalone trend monitoring service that scrapes Reddit for trending topics, enriches them with web research on demand, and exposes an API for Postory (and potentially other clients) to consume personalized trend data.

TrendsRadar has **no knowledge of Postory users**. Personalization (matching trends to user niches) is handled by the consuming client (Postory backend). TrendsRadar is a pure data service.

---

## Data Sources

- **Reddit** public JSON endpoints (no API key required)
- **Web search** (Perplexity 5 results) for on-demand trend enrichment

## Niches

For now, **only one niche: AI**. Remove all other niches (Web Development, Crypto, Gaming). The system must support multiple niches architecturally, but we ship with AI only.

Each niche has:
- `id` — unique identifier
- `name` — display name
- `subreddits` — list of subreddit names to monitor

---

## Trend Collection

### What we collect

For each niche, we scrape **hot Reddit posts per subreddit**.

### Scheduling

- Default interval: **every 30 minutes**, all niches
- Configurable interval via admin UI (dropdown: 15min / 30min / 1h / 2h / 5h / 12h/ 24h)
- Admin can:
  - Start/stop the global scheduler
  - Trigger a manual run (all niches)
  - Start/stop per-niche scheduling independently
  - Trigger a manual run for a specific niche

### Trend lifecycle

Before inserting new trends from a scrape:
1. Mark all existing `active` trends from the same subreddit + source as `expired`
2. Insert new trends as `active`
3. Trends that appear in consecutive scrapes should be **deduplicated** by `reddit_post_id` — update metrics (upvotes, comments) instead of creating duplicates

Expired trends are kept for **30 days**, then deleted by a cleanup job.

---

## Trend Data Model

```
Trend:
  id: UUID
  reddit_post_id: string (unique, for dedup)
  title: string
  subreddit: string
  niche_id: string
  status: "active" | "expired"
  url: string (link to Reddit post)
  upvotes: int
  comment_count: int
  
  # Web research (populated on demand)
  context_summary: text | null (web research result up to 3000 symbols)
  research_done: boolean (default false)
  researched_at: timestamp | null
  
  # Vector embedding
  embedding: vector | null (generated from title + context_summary)
  
  collected_at: timestamp
  expired_at: timestamp | null
```

---

## Web Research (On-Demand Enrichment)

**Web research is NOT done during scraping.** Most trends will never be used for post generation, so researching all of them wastes resources.

### When research happens

When a client requests a specific trend by ID (`GET /api/v1/trends/{id}`):
1. Check if `research_done == true` → return immediately
2. If `research_done == false`:
   - Perform web search (Serper/Brave) for the trend topic
   - Fetch top 3-5 results, extract key facts, numbers, quotes
   - Generate a `context_summary` (500-1000 words) with structured information useful for writing social media posts
   - Generate/update the `embedding` vector from title + context_summary
   - Save to DB, set `research_done = true`
   - Return the enriched trend

The client should expect this endpoint to take **5-15 seconds** on first call for an un-researched trend. Subsequent calls are instant.

### Context summary content

The summary should include:
- What the trend is about (factual explanation)
- Key numbers, statistics, data points
- Notable quotes or opinions
- Why it matters / why people care
- Timeline (when did this start, what happened)

This context will be injected into an LLM prompt for post generation, so it must be **factual and detailed**, not generic.

---

## Vector Embeddings

All trends must be vectorized for semantic search.

### What gets embedded

- **On collection**: generate embedding from `title` only (lightweight, immediate)
- **After web research**: regenerate embedding from `title + context_summary` (richer, more accurate)

### Embedding storage

Use **pgvector** extension for PostgreSQL. Store embeddings in the `Trend` table as a `vector` column.

### Embedding model

Use OpenAI `text-embedding-3-small` or Gemini embeddings (TBD based on cost). Must be consistent — all trends use the same model.

---

## API Endpoints

### Trends

#### `GET /api/v1/trends`
List active trends with filters.

Query params:
- `niche_id` (optional) — filter by niche
- `limit` (default 20, max 100)
- `offset` (default 0)

Returns: list of trends (without `context_summary` to keep payload small)

#### `GET /api/v1/trends/{id}`
Get a single trend with full details.

**This is the endpoint that triggers on-demand web research** if not already done.

Returns: full trend object including `context_summary`

#### `POST /api/v1/trends/search`
Semantic search across all trends.

Body:
```json
{
  "query": "seasonal allergies in children",
  "niche_slug": "ai",           // optional, filter by niche
  "limit": 10
}
```

Backend generates embedding from `query`, performs cosine similarity search against trend embeddings, returns ranked results.

Returns: list of trends with `relevance_score` (0-1)

#### `GET /api/v1/trends/recommended`
Get trends recommended based on a text description (used by Postory to pass user's niche description).

Query params:
- `description` — free-text niche description (e.g., "AI tools for developers")
- `limit` (default 10)

Backend generates embedding from `description`, same as search but framed as recommendations.

Returns: list of trends with `relevance_score`

### Niches

#### `GET /api/v1/niches`
List all niches with subreddit counts.

#### `GET /api/v1/niches/{id}`
Get niche details including subreddit list.

### Admin / Scheduler

#### `GET /api/v1/admin/scheduler/status`
Get scheduler status (running/stopped, interval, last run time, next run time, per-niche status).

#### `POST /api/v1/admin/scheduler/start`
Start the global scheduler.

Body:
```json
{
  "interval_minutes": 30
}
```

#### `POST /api/v1/admin/scheduler/stop`
Stop the global scheduler.

#### `POST /api/v1/admin/scheduler/run`
Trigger an immediate manual run.

Body:
```json
{
  "niche_id": "ai"  // optional, omit for all niches
}
```

#### `POST /api/v1/admin/scheduler/niche/{niche_id}/start`
Start scheduling for a specific niche.

#### `POST /api/v1/admin/scheduler/niche/{niche_id}/stop`
Stop scheduling for a specific niche.

---

## Admin UI

TrendsRadar must have a **web-based admin UI** (not just API). This is for development, testing, and monitoring.

### Pages

#### Dashboard
- Scheduler status (running/stopped, interval, last/next run)
- Per-niche status (active/stopped, trend count, last scraped)
- Quick stats: total active trends, total expired, trends with research

#### Trends Browser
- Table/list of all trends
- Filters: niche, collection type (now/daily/weekly), status (active/expired), researched (yes/no)
- Search bar (text search by title)
- Click on trend → detail view with full context_summary
- Button to manually trigger web research for a trend

#### Niches Management
- List of niches with subreddit counts
- View/edit subreddits per niche
- Add/remove niches (for future expansion)

#### Scheduler Controls
- Dropdown to select interval (15min / 30min / 1h / 2h)
- Start/Stop global scheduler button
- Per-niche start/stop toggles
- "Run Now" button (global or per-niche)
- Log of recent runs (timestamp, niche, trends found, duration)

---

## Tech Stack

- **Backend**: FastAPI (Python) — already in use
- **Database**: PostgreSQL with pgvector extension
- **Task scheduling**: Celery with Redis (already in use) or APScheduler
- **Admin UI**: React or simple Jinja2 templates (TBD — keep it simple)
- **Web search**: Serper API (already have key) or Brave Search API

---

## Summary of Key Decisions

| Decision | Choice |
|----------|--------|
| Niches for now | AI only (others removed) |
| Reddit feeds | Hot per subreddit (now), Top per subreddit (daily/weekly) |
| Scrape interval | Every 30 min (configurable) |
| Web research | On-demand only (when trend requested by ID) |
| Old trends | Mark as expired, delete after 72h |
| Deduplication | By reddit_post_id across scrapes |
| Vector search | pgvector in PostgreSQL |
| Embedding generation | On collection (title only), after research (title + context) |
| Sub-niches | None — use semantic search within niche instead |
| Personalization | Not in TrendsRadar — client (Postory) handles via search/recommended endpoints |

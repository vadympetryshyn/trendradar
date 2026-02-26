# TrendsRadar API

Base URL: `/api/v1`

## Endpoints

### List Trends

```
GET /api/v1/trends
```

**Query Parameters:**

| Parameter         | Type    | Default  | Description                        |
|-------------------|---------|----------|------------------------------------|
| `niche_id`        | int     | —        | Filter by niche                    |
| `collection_type` | string  | —        | Filter: `now`, `daily`, `weekly`   |
| `status`          | string  | `active` | Filter: `active`, `expired`        |
| `limit`           | int     | 20       | Results per page (1–100)           |
| `offset`          | int     | 0        | Pagination offset                  |

**Response:**

```json
{
  "items": [
    {
      "id": "abc-123",
      "niche_id": 1,
      "title": "Trend title",
      "summary": "Short summary",
      "status": "active",
      "sentiment": "positive",
      "category": "technology",
      "key_points": ["point 1", "point 2"],
      "relevance_score": 0.85,
      "collection_type": "now",
      "research_done": false,
      "collected_at": "2025-01-15T12:00:00"
    }
  ],
  "total": 42,
  "limit": 20,
  "offset": 0
}
```

---

### Get Trend Detail

```
GET /api/v1/trends/{trend_id}
```

**Query Parameters:**

| Parameter    | Type | Default | Description                                             |
|--------------|------|---------|---------------------------------------------------------|
| `web_search` | bool | false   | If true and research not done, performs research first   |

**Response:**

```json
{
  "id": "abc-123",
  "niche_id": 1,
  "title": "Trend title",
  "summary": "Short summary",
  "source_post_ids": ["post-1", "post-2"],
  "status": "active",
  "sentiment": "positive",
  "category": "technology",
  "key_points": ["point 1", "point 2"],
  "source_urls": ["https://reddit.com/r/example/..."],
  "source_subreddits": ["technology", "programming"],
  "mention_count": 5,
  "relevance_score": 0.85,
  "collection_type": "now",
  "research_done": true,
  "collected_at": "2025-01-15T12:00:00",
  "context_summary": "Detailed research context...",
  "research_citations": ["https://example.com/source"],
  "researched_at": "2025-01-15T13:00:00",
  "expired_at": null
}
```

---

### Search Trends (Semantic)

```
POST /api/v1/trends/search
```

**Request Body:**

```json
{
  "query": "AI tools for developers",
  "niche_id": 1,
  "limit": 10
}
```

Only `query` is required. `niche_id` and `limit` are optional.

**Response:**

```json
{
  "results": [
    {
      "id": "abc-123",
      "title": "Trend title",
      "summary": "Short summary",
      "sentiment": "positive",
      "category": "technology",
      "relevance_score": 0.85,
      "collection_type": "now",
      "similarity": 0.9231,
      "collected_at": "2025-01-15T12:00:00"
    }
  ],
  "query": "AI tools for developers"
}
```

---

### List Niches

```
GET /api/v1/niches
```

Returns all active niches (without subreddit details).

**Response:**

```json
[
  {
    "id": 1,
    "name": "AI & Machine Learning",
    "slug": "ai-ml",
    "description": "Artificial intelligence and ML trends",
    "is_active": true,
    "created_at": "2025-01-01T00:00:00"
  }
]
```

| Field         | Type     | Description                  |
|---------------|----------|------------------------------|
| `id`          | int      | Niche ID                     |
| `name`        | string   | Display name                 |
| `slug`        | string   | URL-friendly identifier      |
| `description` | string   | Short description            |
| `is_active`   | bool     | Whether the niche is active  |
| `created_at`  | datetime | Creation timestamp           |

---

### List Collection Types

```
GET /api/v1/niches/collection-types
```

Returns the available trend collection types.

**Response:**

```json
[
  { "value": "now", "label": "Trends Now" },
  { "value": "daily", "label": "Trends Today" },
  { "value": "weekly", "label": "Trends This Week" }
]
```

| Field   | Type   | Description                                      |
|---------|--------|--------------------------------------------------|
| `value` | string | Collection type value to use in API queries       |
| `label` | string | Human-readable label                              |


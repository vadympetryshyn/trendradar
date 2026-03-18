# TrendRadar API

Base URL: `/api/v1`

## Endpoints

### List Trends

```
GET /api/v1/trends
```

**Query Parameters:**

| Parameter         | Type    | Default  | Description                        |
|-------------------|---------|----------|------------------------------------|
| `niche`           | string  | —        | Filter by niche slug (e.g. `ai-ml`) |
| `collection_type` | string  | —        | Filter: `now`, `rising`, `daily`, `weekly` |
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

**Example:**

```
GET /api/v1/trends?niche=ai-ml&collection_type=now
GET /api/v1/trends?niche=ai-ml&collection_type=daily&limit=10
```

---

### Random Trends

```
GET /api/v1/trends/random
```

Returns random active trends for a given collection type, mixed across all niches.

**Query Parameters:**

| Parameter         | Type   | Default | Description                                    |
|-------------------|--------|---------|------------------------------------------------|
| `collection_type` | string | —       | **Required.** Trend type: `now`, `rising`, `daily`, `weekly` |
| `limit`           | int    | 20      | Results per page (1–100)                       |
| `offset`          | int    | 0       | Pagination offset                              |

**Example:**

```
GET /api/v1/trends/random?collection_type=rising
GET /api/v1/trends/random?collection_type=daily&limit=10
```

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
      "collection_type": "rising",
      "research_done": false,
      "collected_at": "2025-01-15T12:00:00"
    }
  ],
  "total": 42,
  "limit": 20,
  "offset": 0
}
```

**Notes:**
- `collection_type` is required — returns `422` if missing
- Results are randomly ordered on each request
- Only returns `active` trends

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
  "niche": "ai-ml",
  "limit": 10
}
```

Only `query` is required. `niche` and `limit` are optional.

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

### Search Trends by Vector

```
POST /api/v1/trends/search-by-vector
```

Find the most relevant trends using a pre-computed embedding vector. This skips the embedding generation step, making it faster and ideal for services that already have vectorized data (e.g. Postory).

By default searches only `now` and `daily` trends and returns 5 results.

**Request Body:**

```json
{
  "embedding": [0.0123, -0.0456, 0.0789, "... (1536 floats)"],
  "collection_types": ["now", "daily"],
  "niche": "ai-ml",
  "limit": 5
}
```

| Field              | Type         | Required | Default            | Description                                  |
|--------------------|--------------|----------|--------------------|----------------------------------------------|
| `embedding`        | float[]      | yes      | —                  | Pre-computed embedding vector (1536 dimensions, OpenAI `text-embedding-3-small` compatible) |
| `collection_types` | string[]     | no       | `["now", "daily"]` | Which trend types to search: `now`, `rising`, `daily`, `weekly` |
| `niche`            | string       | no       | —                  | Filter by niche slug (e.g. `ai-ml`)          |
| `limit`            | int          | no       | 5                  | Number of results to return (1–20)           |
| `random`           | int          | no       | —                  | If set, fetches top 10 results and returns this many randomly picked from them (1–10). Useful for adding variety while staying relevant. |

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
  "query": "vector_search"
}
```

**Example (Python):**

```python
import requests

response = requests.post(
    "https://your-api/api/v1/trends/search-by-vector",
    json={
        "embedding": user_niche_vector,  # 1536-dim float list
        "limit": 5,
    },
)
trends = response.json()["results"]
```

**Notes:**
- The embedding must be 1536 dimensions (matching OpenAI `text-embedding-3-small`). A `422` error is returned if the dimension count is wrong.
- Similarity is cosine similarity (0–1, higher = more relevant).
- When `random` is set, the endpoint always fetches the top 10 most similar results, then randomly selects `random` of them. The `limit` parameter is ignored in this case.

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
  { "value": "rising", "label": "Rising Trends" },
  { "value": "daily", "label": "Trends Today" },
  { "value": "weekly", "label": "Trends This Week" }
]
```

| Field   | Type   | Description                                      |
|---------|--------|--------------------------------------------------|
| `value` | string | Collection type value to use in API queries       |
| `label` | string | Human-readable label                              |


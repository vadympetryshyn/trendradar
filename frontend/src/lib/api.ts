import type {
  Niche,
  TrendListResponse,
  TrendDetail,
  TrendSearchResponse,
  SchedulerStatus,
  ManualTriggerResponse,
  DashboardStats,
  NicheScheduleStatus,
  CollectionTask,
  CollectionTaskList,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3006";

async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `API error: ${res.status}`);
  }
  return res.json();
}

// ── Niches ──────────────────────────────────────────────────────────

export function getNiches(): Promise<Niche[]> {
  return fetchApi("/api/v1/niches");
}

// ── Trends ──────────────────────────────────────────────────────────

export function getTrends(params?: {
  niche_id?: number;
  status?: string;
  collection_type?: string;
  research_done?: boolean;
  has_embedding?: boolean;
  limit?: number;
  offset?: number;
}): Promise<TrendListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.niche_id) searchParams.set("niche_id", String(params.niche_id));
  if (params?.status) searchParams.set("status", String(params.status));
  if (params?.collection_type) searchParams.set("collection_type", params.collection_type);
  if (params?.research_done !== undefined) searchParams.set("research_done", String(params.research_done));
  if (params?.has_embedding !== undefined) searchParams.set("has_embedding", String(params.has_embedding));
  if (params?.limit) searchParams.set("limit", String(params.limit));
  if (params?.offset) searchParams.set("offset", String(params.offset));
  const qs = searchParams.toString();
  return fetchApi(`/api/v1/trends${qs ? `?${qs}` : ""}`);
}

export function getTrend(id: string, webSearch = false): Promise<TrendDetail> {
  const qs = webSearch ? "?web_search=true" : "";
  return fetchApi(`/api/v1/trends/${id}${qs}`);
}

export function searchTrends(
  query: string,
  nicheId?: number,
  limit?: number
): Promise<TrendSearchResponse> {
  return fetchApi("/api/v1/trends/search", {
    method: "POST",
    body: JSON.stringify({
      query,
      niche_id: nicheId,
      limit: limit || 20,
    }),
  });
}

export function getRecommended(
  description: string,
  limit?: number
): Promise<TrendSearchResponse> {
  const params = new URLSearchParams({
    description,
    limit: String(limit || 5),
  });
  return fetchApi(`/api/v1/trends/recommended?${params}`);
}

// ── Scheduler ───────────────────────────────────────────────────────

export function getSchedulerStatus(): Promise<SchedulerStatus> {
  return fetchApi("/api/v1/admin/scheduler/status");
}

export function startScheduler(
  intervalMinutes: number
): Promise<SchedulerStatus> {
  return fetchApi("/api/v1/admin/scheduler/start", {
    method: "POST",
    body: JSON.stringify({ interval_minutes: intervalMinutes }),
  });
}

export function stopScheduler(): Promise<SchedulerStatus> {
  return fetchApi("/api/v1/admin/scheduler/stop", { method: "POST" });
}

export function runNow(nicheId?: number, collectionType?: string): Promise<ManualTriggerResponse> {
  return fetchApi("/api/v1/admin/scheduler/run", {
    method: "POST",
    body: JSON.stringify({
      niche_id: nicheId || null,
      collection_type: collectionType || null,
    }),
  });
}

export function startNicheSchedule(
  nicheId: number,
  collectionType: string = "now"
): Promise<NicheScheduleStatus> {
  return fetchApi(`/api/v1/admin/scheduler/niche/${nicheId}/start?collection_type=${collectionType}`, {
    method: "POST",
  });
}

export function stopNicheSchedule(
  nicheId: number,
  collectionType: string = "now"
): Promise<NicheScheduleStatus> {
  return fetchApi(`/api/v1/admin/scheduler/niche/${nicheId}/stop?collection_type=${collectionType}`, {
    method: "POST",
  });
}

// ── Tasks ───────────────────────────────────────────────────────────

export function getCollectionTasks(
  page = 1,
  perPage = 20,
  status?: string
): Promise<CollectionTaskList> {
  const params = new URLSearchParams({
    page: String(page),
    per_page: String(perPage),
  });
  if (status) params.set("status", status);
  return fetchApi(`/api/v1/admin/tasks?${params}`);
}

export function getCollectionTask(id: number): Promise<CollectionTask> {
  return fetchApi(`/api/v1/admin/tasks/${id}`);
}

export function stopCollectionTask(id: number): Promise<CollectionTask> {
  return fetchApi(`/api/v1/admin/tasks/${id}/stop`, { method: "POST" });
}

export function deleteCollectionTask(
  id: number
): Promise<{ detail: string }> {
  return fetchApi(`/api/v1/admin/tasks/${id}`, { method: "DELETE" });
}

export function deleteCollectionTasksBulk(
  ids: number[]
): Promise<{ detail: string }> {
  return fetchApi("/api/v1/admin/tasks/bulk", {
    method: "DELETE",
    body: JSON.stringify({ ids }),
  });
}

export function deleteTrendsBulk(
  ids: string[]
): Promise<{ detail: string }> {
  return fetchApi("/api/v1/trends/bulk", {
    method: "DELETE",
    body: JSON.stringify({ ids }),
  });
}

export function deleteExpiredTrends(): Promise<{ detail: string }> {
  return fetchApi("/api/v1/admin/trends/expired", { method: "DELETE" });
}

// ── Stats ───────────────────────────────────────────────────────────

export function getDashboardStats(): Promise<DashboardStats> {
  return fetchApi("/api/v1/admin/stats");
}

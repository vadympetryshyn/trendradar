import type {
  Niche,
  TrendAnalysis,
  PaginatedHistory,
  PaginatedAnalyses,
  PaginatedTasks,
  ManualTriggerResponse,
  ScheduleConfig,
  TaskStatus,
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

export function getNiches(): Promise<Niche[]> {
  return fetchApi("/api/v1/niches");
}

export function getLatestTrends(nicheSlug: string): Promise<TrendAnalysis> {
  return fetchApi(`/api/v1/trends/${nicheSlug}`);
}

export function getAnalysisHistory(
  nicheSlug: string,
  page = 1,
  perPage = 10
): Promise<PaginatedHistory> {
  return fetchApi(
    `/api/v1/trends/${nicheSlug}/history?page=${page}&per_page=${perPage}`
  );
}

export function triggerAnalysis(
  nicheSlug: string
): Promise<ManualTriggerResponse> {
  return fetchApi(`/api/v1/admin/analyze/${nicheSlug}`, { method: "POST" });
}

export function getTaskStatus(taskId: string): Promise<TaskStatus> {
  return fetchApi(`/api/v1/admin/task/${taskId}/status`);
}

export function triggerAllAnalyses(): Promise<{
  triggered: number;
  tasks: { task_id: string; niche_slug: string; niche_name: string }[];
}> {
  return fetchApi("/api/v1/admin/analyze-all", { method: "POST" });
}

export function stopTask(taskId: string): Promise<{ detail: string }> {
  return fetchApi(`/api/v1/admin/task/${taskId}/stop`, { method: "POST" });
}

export function stopAllTasks(): Promise<{ detail: string; stopped: number }> {
  return fetchApi("/api/v1/admin/tasks/stop-all", { method: "POST" });
}

export function getSchedules(): Promise<ScheduleConfig[]> {
  return fetchApi("/api/v1/admin/schedules");
}

export function createSchedule(data: {
  niche_id: number;
  interval_minutes?: number;
  is_enabled?: boolean;
}): Promise<ScheduleConfig> {
  return fetchApi("/api/v1/admin/schedules", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateSchedule(
  scheduleId: number,
  data: { interval_minutes?: number; is_enabled?: boolean }
): Promise<ScheduleConfig> {
  return fetchApi(`/api/v1/admin/schedules/${scheduleId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export function deleteSchedule(scheduleId: number): Promise<{ detail: string }> {
  return fetchApi(`/api/v1/admin/schedules/${scheduleId}`, {
    method: "DELETE",
  });
}

export function getAnalysisById(id: number): Promise<TrendAnalysis> {
  return fetchApi(`/api/v1/admin/analyses/${id}`);
}

export function getAnalyses(
  page = 1,
  perPage = 20,
  status?: string
): Promise<PaginatedAnalyses> {
  const params = new URLSearchParams({
    page: String(page),
    per_page: String(perPage),
  });
  if (status) params.set("status", status);
  return fetchApi(`/api/v1/admin/analyses?${params}`);
}

export function getTasks(page = 1, perPage = 20): Promise<PaginatedTasks> {
  return fetchApi(
    `/api/v1/admin/tasks?page=${page}&per_page=${perPage}`
  );
}

export function deleteAnalysis(id: number): Promise<{ detail: string }> {
  return fetchApi(`/api/v1/admin/analyses/${id}`, { method: "DELETE" });
}

export function deleteTask(id: number): Promise<{ detail: string }> {
  return fetchApi(`/api/v1/admin/tasks/${id}`, { method: "DELETE" });
}

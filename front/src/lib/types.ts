export interface Niche {
  id: number;
  name: string;
  slug: string;
  description: string;
  subreddits: string[];
  is_active: boolean;
  created_at: string;
}

export interface Trend {
  id: string;
  niche_id: number;
  title: string;
  summary: string;
  source_post_ids: string[];
  status: "active" | "expired";
  sentiment: string;
  category: string;
  key_points: string[];
  source_urls: string[];
  mention_urls: string[];
  source_subreddits: string[];
  mention_count: number;
  relevance_score: number;
  collection_type: "now" | "daily" | "weekly";
  research_done: boolean;
  has_embedding: boolean;
  collected_at: string;
}

export interface TrendDetail extends Trend {
  context_summary: string | null;
  research_citations: string[];
  researched_at: string | null;
  expired_at: string | null;
}

export interface TrendListResponse {
  items: Trend[];
  total: number;
  limit: number;
  offset: number;
}

export interface TrendSearchResult {
  id: string;
  title: string;
  summary: string;
  source_post_ids: string[];
  sentiment: string;
  category: string;
  relevance_score: number;
  collection_type: "now" | "daily" | "weekly";
  similarity: number;
  collected_at: string;
}

export interface TrendSearchResponse {
  results: TrendSearchResult[];
  query: string;
}

export interface NicheScheduleStatus {
  niche_id: number;
  niche_name: string;
  niche_slug: string;
  collection_type: "now" | "daily" | "weekly";
  is_enabled: boolean;
  interval_minutes: number;
  last_run_at: string | null;
  next_run_at: string | null;
  trend_count: number;
}

export interface SchedulerStatus {
  running: boolean;
  niches: NicheScheduleStatus[];
}

export interface DashboardStats {
  active_trends: number;
  expired_trends: number;
  researched_trends: number;
  embedded_trends: number;
  total_niches: number;
}

export interface ManualTriggerResponse {
  message: string;
  niche_id: number | null;
  niche_name: string | null;
}

export interface CollectionTask {
  id: number;
  niche_id: number;
  niche_name: string;
  niche_slug: string;
  collection_type: "now" | "daily" | "weekly";
  celery_task_id: string | null;
  status: "queued" | "running" | "completed" | "failed" | "stopped";
  trends_created: number;
  trends_expired: number;
  error_message: string | null;
  started_at: string;
  completed_at: string | null;
}

export interface CollectionTaskList {
  items: CollectionTask[];
  total: number;
  page: number;
  per_page: number;
}

export interface UserResponse {
  id: string;
  email: string;
  name: string | null;
  is_email_verified: boolean;
  is_admin: boolean;
  has_password: boolean;
  created_at: string;
  updated_at: string;
}

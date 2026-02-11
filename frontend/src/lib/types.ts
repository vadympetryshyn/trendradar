export interface Niche {
  id: number;
  name: string;
  slug: string;
  subreddits: string[];
  is_active: boolean;
  created_at: string;
}

export interface TrendItem {
  id: number;
  title: string;
  summary: string;
  sentiment: string;
  sentiment_score: number;
  category: string;
  key_points: string[];
  source_urls: string[];
  source_subreddits: string[];
  mention_count: number;
  relevance_score: number;
}

export interface TrendAnalysis {
  id: number;
  niche_id: number;
  status: string;
  overall_summary: string | null;
  posts_fetched: number;
  subreddits_fetched: number;
  error_message: string | null;
  started_at: string;
  completed_at: string | null;
  trend_items: TrendItem[];
}

export interface TrendAnalysisSummary {
  id: number;
  niche_id: number;
  status: string;
  overall_summary: string | null;
  posts_fetched: number;
  subreddits_fetched: number;
  error_message: string | null;
  started_at: string;
  completed_at: string | null;
}

export interface PaginatedHistory {
  items: TrendAnalysisSummary[];
  total: number;
  page: number;
  per_page: number;
}

export interface ScheduleConfig {
  id: number;
  niche_id: number;
  niche_name: string | null;
  niche_slug: string | null;
  interval_minutes: number;
  is_enabled: boolean;
  last_run_at: string | null;
  next_run_at: string | null;
  updated_at: string;
}

export interface ManualTriggerResponse {
  task_id: string;
  message: string;
  niche_slug: string;
}

export interface TaskStatus {
  task_id: string;
  status: string;
  analysis_id: number | null;
  posts_fetched: number;
  subreddits_fetched: number;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
}

export interface AnalysisListItem {
  id: number;
  niche_name: string;
  niche_slug: string;
  status: string;
  overall_summary: string | null;
  posts_fetched: number;
  subreddits_fetched: number;
  error_message: string | null;
  celery_task_id: string | null;
  started_at: string | null;
  completed_at: string | null;
  trend_items_count: number;
}

export interface PaginatedAnalyses {
  items: AnalysisListItem[];
  total: number;
  page: number;
  per_page: number;
}

export interface TaskListItem {
  id: number;
  celery_task_id: string | null;
  niche_name: string;
  niche_slug: string;
  status: string;
  posts_fetched: number;
  subreddits_fetched: number;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
}

export interface PaginatedTasks {
  items: TaskListItem[];
  total: number;
  page: number;
  per_page: number;
}

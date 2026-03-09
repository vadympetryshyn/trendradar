import { fetchApi } from "./api";

export interface CpuMetrics {
  percent: number;
  count: number;
  count_logical: number;
  per_core_percent: number[];
}

export interface MemoryMetrics {
  total_mb: number;
  used_mb: number;
  available_mb: number;
  percent: number;
}

export interface DiskMetrics {
  total_gb: number;
  used_gb: number;
  free_gb: number;
  percent: number;
}

export interface ContainerMetrics {
  name: string;
  status: string;
  cpu_percent: number;
  memory_mb: number;
  memory_limit_mb: number;
  memory_percent: number;
}

export interface ServerMetrics {
  cpu: CpuMetrics;
  memory: MemoryMetrics;
  disk: DiskMetrics;
  containers: ContainerMetrics[];
  uptime_seconds: number;
  docker_available: boolean;
}

export function getServerMetrics(): Promise<ServerMetrics> {
  return fetchApi<ServerMetrics>("/api/v1/admin/metrics");
}

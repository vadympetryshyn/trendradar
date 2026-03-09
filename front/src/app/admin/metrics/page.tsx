"use client";

import { useState, useEffect, useCallback } from "react";
import { Loader2, RefreshCw, Cpu, MemoryStick, HardDrive, Box, ChevronDown } from "lucide-react";
import { getServerMetrics, ServerMetrics } from "@/lib/admin-metrics";
import { cn } from "@/lib/utils";

const POLL_INTERVAL = 3000;

function formatUptime(seconds: number): string {
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (d > 0) return `${d}d ${h}h ${m}m`;
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

function ProgressBar({ percent, color }: { percent: number; color: string }) {
  const clamped = Math.min(100, Math.max(0, percent));
  return (
    <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
      <div
        className={cn("h-full rounded-full transition-all duration-500", color)}
        style={{ width: `${clamped}%` }}
      />
    </div>
  );
}

function barColor(percent: number): string {
  if (percent >= 90) return "bg-red-500";
  if (percent >= 70) return "bg-yellow-500";
  return "bg-green-500";
}

function MetricCard({
  icon: Icon,
  title,
  children,
}: {
  icon: React.ElementType;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-xl bg-card border border-border p-5">
      <div className="flex items-center gap-2 mb-4">
        <span className="flex size-8 items-center justify-center rounded-lg bg-accent/10">
          <Icon className="size-4 text-accent" />
        </span>
        <h3 className="font-semibold text-sm">{title}</h3>
      </div>
      {children}
    </div>
  );
}

function CoreGrid({ cores, label }: { cores: number[]; label?: string }) {
  return (
    <div className="mt-3">
      {label && <p className="text-xs text-muted-foreground mb-2 font-medium">{label}</p>}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        {cores.map((pct, i) => (
          <div key={i} className="rounded-lg bg-muted/50 p-2">
            <div className="flex justify-between text-xs mb-1">
              <span className="text-muted-foreground">Core {i}</span>
              <span className="font-medium">{pct}%</span>
            </div>
            <ProgressBar percent={pct} color={barColor(pct)} />
          </div>
        ))}
      </div>
    </div>
  );
}

export default function AdminMetricsPage() {
  const [metrics, setMetrics] = useState<ServerMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [cpuExpanded, setCpuExpanded] = useState(false);
  const [expandedContainer, setExpandedContainer] = useState<string | null>(null);

  const fetchMetrics = useCallback(async () => {
    try {
      const data = await getServerMetrics();
      setMetrics(data);
      setLastUpdated(new Date());
      setError(null);
    } catch {
      setError("Failed to load metrics");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, POLL_INTERVAL);
    return () => clearInterval(interval);
  }, [fetchMetrics]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="size-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error || !metrics) {
    return (
      <div className="p-6 lg:p-8 max-w-6xl mx-auto">
        <p className="text-destructive">{error ?? "No data"}</p>
      </div>
    );
  }

  const { cpu, memory, disk, containers, uptime_seconds, docker_available } = metrics;

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold mb-1">Server Metrics</h1>
          <p className="text-muted-foreground text-sm">
            Uptime: {formatUptime(uptime_seconds)}
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground mt-1">
          <RefreshCw className="size-3 animate-spin" style={{ animationDuration: "3s" }} />
          {lastUpdated && (
            <span>Updated {lastUpdated.toLocaleTimeString()}</span>
          )}
        </div>
      </div>

      {/* System metrics */}
      <div className="grid sm:grid-cols-3 gap-4 mb-6">
        {/* CPU */}
        <div
          className={cn(
            "rounded-xl bg-card border border-border p-5 cursor-pointer hover:border-accent/40 transition-colors",
            cpuExpanded && "sm:col-span-3"
          )}
          onClick={() => setCpuExpanded(!cpuExpanded)}
        >
          <div className="flex items-center gap-2 mb-4">
            <span className="flex size-8 items-center justify-center rounded-lg bg-accent/10">
              <Cpu className="size-4 text-accent" />
            </span>
            <h3 className="font-semibold text-sm">CPU</h3>
            <ChevronDown
              className={cn(
                "size-4 ml-auto text-muted-foreground transition-transform",
                cpuExpanded && "rotate-180"
              )}
            />
          </div>
          <div className="mb-3">
            <div className="flex justify-between items-baseline mb-1.5">
              <span className="text-2xl font-bold">{cpu.percent}%</span>
              <span className="text-xs text-muted-foreground">
                {cpu.count} cores / {cpu.count_logical} threads
              </span>
            </div>
            <ProgressBar percent={cpu.percent} color={barColor(cpu.percent)} />
          </div>
          {cpuExpanded && cpu.per_core_percent.length > 0 && (
            <CoreGrid cores={cpu.per_core_percent} label="Server per-core load" />
          )}
        </div>

        {/* Memory */}
        <MetricCard icon={MemoryStick} title="Memory">
          <div className="mb-3">
            <div className="flex justify-between items-baseline mb-1.5">
              <span className="text-2xl font-bold">{memory.percent}%</span>
              <span className="text-xs text-muted-foreground">
                {(memory.used_mb / 1024).toFixed(1)} / {(memory.total_mb / 1024).toFixed(1)} GB
              </span>
            </div>
            <ProgressBar percent={memory.percent} color={barColor(memory.percent)} />
          </div>
          <p className="text-xs text-muted-foreground">
            Free: {(memory.available_mb / 1024).toFixed(1)} GB
          </p>
        </MetricCard>

        {/* Disk */}
        <MetricCard icon={HardDrive} title="Disk">
          <div className="mb-3">
            <div className="flex justify-between items-baseline mb-1.5">
              <span className="text-2xl font-bold">{disk.percent}%</span>
              <span className="text-xs text-muted-foreground">
                {disk.used_gb} / {disk.total_gb} GB
              </span>
            </div>
            <ProgressBar percent={disk.percent} color={barColor(disk.percent)} />
          </div>
          <p className="text-xs text-muted-foreground">Free: {disk.free_gb} GB</p>
        </MetricCard>
      </div>

      {/* Docker containers */}
      <div className="rounded-xl bg-card border border-border p-5">
        <div className="flex items-center gap-2 mb-4">
          <span className="flex size-8 items-center justify-center rounded-lg bg-accent/10">
            <Box className="size-4 text-accent" />
          </span>
          <h3 className="font-semibold text-sm">Docker Containers</h3>
          {!docker_available && (
            <span className="ml-auto text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded-full">
              Socket unavailable
            </span>
          )}
        </div>

        {!docker_available ? (
          <p className="text-sm text-muted-foreground">
            Docker socket not accessible. Make sure{" "}
            <code className="text-xs bg-muted px-1 rounded">/var/run/docker.sock</code> is mounted
            and the container has the correct group permissions.
          </p>
        ) : containers.length === 0 ? (
          <p className="text-sm text-muted-foreground">No running containers.</p>
        ) : (
          <div className="space-y-3">
            {/* Header row */}
            <div className="grid grid-cols-[1fr_auto_120px_120px] gap-4 text-xs text-muted-foreground px-1">
              <span>Name</span>
              <span>Status</span>
              <span>CPU</span>
              <span>Memory</span>
            </div>
            {containers.map((c) => (
              <div key={c.name}>
                <div
                  className="grid grid-cols-[1fr_auto_120px_120px] gap-4 items-center p-3 rounded-lg bg-muted/30 border border-border/50 cursor-pointer hover:bg-muted/50"
                  onClick={() =>
                    setExpandedContainer(expandedContainer === c.name ? null : c.name)
                  }
                >
                  {/* Name */}
                  <div className="flex items-center gap-1.5 min-w-0">
                    <span className="font-mono text-sm font-medium truncate">{c.name}</span>
                    <ChevronDown
                      className={cn(
                        "size-3 shrink-0 text-muted-foreground transition-transform",
                        expandedContainer === c.name && "rotate-180"
                      )}
                    />
                  </div>

                  {/* Status badge */}
                  <span
                    className={cn(
                      "text-xs px-2 py-0.5 rounded-full whitespace-nowrap",
                      c.status.startsWith("Up")
                        ? "bg-green-500/10 text-green-600"
                        : "bg-red-500/10 text-red-500"
                    )}
                  >
                    {c.status}
                  </span>

                  {/* CPU */}
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span>{c.cpu_percent}%</span>
                    </div>
                    <ProgressBar percent={c.cpu_percent} color={barColor(c.cpu_percent)} />
                  </div>

                  {/* Memory */}
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span>{c.memory_percent}%</span>
                      <span className="text-muted-foreground">{c.memory_mb} MB</span>
                    </div>
                    <ProgressBar percent={c.memory_percent} color={barColor(c.memory_percent)} />
                  </div>
                </div>
                {expandedContainer === c.name && (
                  <div className="px-3 pb-3 pt-2 rounded-b-lg bg-muted/20 border border-t-0 border-border/50">
                    <div className="grid grid-cols-2 gap-4">
                      {/* CPU detail */}
                      <div>
                        <p className="text-xs text-muted-foreground font-medium mb-2">CPU Details</p>
                        <div className="rounded-lg bg-muted/50 p-3 space-y-2">
                          <div className="flex justify-between text-xs">
                            <span className="text-muted-foreground">Container usage</span>
                            <span className="font-medium">{c.cpu_percent}%</span>
                          </div>
                          <ProgressBar percent={c.cpu_percent} color={barColor(c.cpu_percent)} />
                        </div>
                      </div>
                      {/* Memory detail */}
                      <div>
                        <p className="text-xs text-muted-foreground font-medium mb-2">Memory Details</p>
                        <div className="space-y-2">
                          <div className="rounded-lg bg-muted/50 p-3 space-y-2">
                            <div className="flex justify-between text-xs">
                              <span className="text-muted-foreground">Used</span>
                              <span className="font-medium">{c.memory_mb} MB</span>
                            </div>
                            <div className="flex justify-between text-xs">
                              <span className="text-muted-foreground">Limit</span>
                              <span className="font-medium">
                                {c.memory_limit_mb > 1024
                                  ? `${(c.memory_limit_mb / 1024).toFixed(1)} GB`
                                  : `${c.memory_limit_mb} MB`}
                              </span>
                            </div>
                            <div className="flex justify-between text-xs">
                              <span className="text-muted-foreground">Usage</span>
                              <span className="font-medium">{c.memory_percent}%</span>
                            </div>
                            <ProgressBar percent={c.memory_percent} color={barColor(c.memory_percent)} />
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

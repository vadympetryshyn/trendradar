"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  getNiches,
  getSchedules,
  getTaskStatus,
  triggerAnalysis,
} from "@/lib/api";
import type { Niche, ScheduleConfig, TaskStatus } from "@/lib/types";
import { StatusBadge } from "./_components/status-badge";

export default function AdminPage() {
  const [niches, setNiches] = useState<Niche[]>([]);
  const [schedules, setSchedules] = useState<ScheduleConfig[]>([]);
  const [taskStatuses, setTaskStatuses] = useState<Record<string, TaskStatus>>({});
  const [loading, setLoading] = useState(true);
  const pollIntervals = useRef<Record<string, ReturnType<typeof setInterval>>>({});

  const stopPolling = useCallback((slug: string) => {
    if (pollIntervals.current[slug]) {
      clearInterval(pollIntervals.current[slug]);
      delete pollIntervals.current[slug];
    }
  }, []);

  const startPolling = useCallback((slug: string, taskId: string) => {
    stopPolling(slug);

    const poll = async () => {
      try {
        const status = await getTaskStatus(taskId);
        setTaskStatuses((prev) => ({ ...prev, [slug]: status }));
        if (status.status === "completed" || status.status === "failed") {
          stopPolling(slug);
        }
      } catch {
        stopPolling(slug);
      }
    };

    poll();
    pollIntervals.current[slug] = setInterval(poll, 2000);
  }, [stopPolling]);

  useEffect(() => {
    Promise.all([getNiches(), getSchedules()])
      .then(([nichesData, schedulesData]) => {
        setNiches(nichesData);
        setSchedules(schedulesData);
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    return () => {
      Object.values(pollIntervals.current).forEach(clearInterval);
    };
  }, []);

  const handleTrigger = async (slug: string) => {
    setTaskStatuses((prev) => ({
      ...prev,
      [slug]: { task_id: "", status: "queued", analysis_id: null, posts_fetched: 0, subreddits_fetched: 0, error_message: null, started_at: null, completed_at: null },
    }));
    try {
      const result = await triggerAnalysis(slug);
      setTaskStatuses((prev) => ({
        ...prev,
        [slug]: { ...prev[slug], task_id: result.task_id },
      }));
      startPolling(slug, result.task_id);
    } catch (err) {
      setTaskStatuses((prev) => ({
        ...prev,
        [slug]: { ...prev[slug], status: "failed", error_message: err instanceof Error ? err.message : "Failed to trigger" },
      }));
    }
  };

  const isRunning = (slug: string) => {
    const s = taskStatuses[slug];
    return s && !["completed", "failed"].includes(s.status);
  };

  const anyRunning = niches.some((n) => isRunning(n.slug));

  const handleTriggerAll = () => {
    for (const niche of niches) {
      if (!isRunning(niche.slug)) {
        handleTrigger(niche.slug);
      }
    }
  };

  if (loading) {
    return <div className="py-8 text-center text-muted-foreground">Loading...</div>;
  }

  const activeSchedules = schedules.filter((s) => s.is_enabled);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Admin Panel</h1>
        <p className="text-muted-foreground mt-1">
          Manage analysis triggers and schedules
        </p>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <div className="space-y-1.5">
            <CardTitle>Manual Analysis</CardTitle>
            <CardDescription>
              Trigger a new trend analysis for any niche
            </CardDescription>
          </div>
          <Button onClick={handleTriggerAll} disabled={anyRunning}>
            {anyRunning ? "Running..." : "Run All"}
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          {niches.map((niche) => {
            const status = taskStatuses[niche.slug];
            const running = isRunning(niche.slug);

            return (
              <div key={niche.slug} className="space-y-2">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <span className="font-medium">{niche.name}</span>
                    <span className="text-sm text-muted-foreground ml-2">
                      ({niche.subreddits.length} subreddits)
                    </span>
                  </div>
                  <Button
                    size="sm"
                    onClick={() => handleTrigger(niche.slug)}
                    disabled={running}
                  >
                    {running ? "Running..." : "Run Analysis"}
                  </Button>
                </div>

                {status && (
                  <div className="rounded-lg border bg-muted/30 px-4 py-3 space-y-2">
                    <div className="flex items-center justify-between">
                      <StatusBadge status={status.status} />
                      {status.task_id && (
                        <span className="text-[10px] font-mono text-muted-foreground">
                          {status.task_id.slice(0, 8)}
                        </span>
                      )}
                    </div>

                    {(status.posts_fetched > 0 || status.subreddits_fetched > 0) && (
                      <div className="flex gap-4 text-xs text-muted-foreground">
                        <span>{status.posts_fetched} posts fetched</span>
                        <span>{status.subreddits_fetched} subreddits</span>
                      </div>
                    )}

                    {status.error_message && (
                      <p className="text-xs text-red-600">{status.error_message}</p>
                    )}

                    {status.status === "completed" && status.completed_at && (
                      <p className="text-xs text-green-600">
                        Completed at {new Date(status.completed_at).toLocaleTimeString()}
                      </p>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <div className="space-y-1.5">
            <CardTitle>Active Schedules</CardTitle>
            <CardDescription>
              {activeSchedules.length} of {schedules.length} schedule{schedules.length === 1 ? "" : "s"} enabled
            </CardDescription>
          </div>
          <Button variant="outline" size="sm" asChild>
            <Link href="/admin/schedules">Manage Schedules</Link>
          </Button>
        </CardHeader>
        {activeSchedules.length > 0 && (
          <CardContent>
            <div className="space-y-2">
              {activeSchedules.map((s) => (
                <div
                  key={s.id}
                  className="flex items-center justify-between text-sm"
                >
                  <span className="font-medium">
                    {s.niche_name || `Niche #${s.niche_id}`}
                  </span>
                  <span className="text-muted-foreground">
                    Every {s.interval_minutes} min
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        )}
      </Card>
    </div>
  );
}

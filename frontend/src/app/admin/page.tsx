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
  getDashboardStats,
  getSchedulerStatus,
  getCollectionTasks,
  runNow,
  startScheduler,
  stopScheduler,
  startNicheSchedule,
  stopNicheSchedule,
} from "@/lib/api";
import type {
  CollectionTask,
  DashboardStats,
  SchedulerStatus,
} from "@/lib/types";

const STATUS_COLORS: Record<string, string> = {
  queued: "bg-gray-100 text-gray-700",
  running: "bg-blue-100 text-blue-700",
  completed: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
  stopped: "bg-yellow-100 text-yellow-700",
};

export default function AdminPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [scheduler, setScheduler] = useState<SchedulerStatus | null>(null);
  const [recentTasks, setRecentTasks] = useState<CollectionTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [runningNiches, setRunningNiches] = useState<Set<number>>(new Set());
  const [runningAll, setRunningAll] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchData = useCallback(() => {
    return Promise.all([
      getDashboardStats(),
      getSchedulerStatus(),
      getCollectionTasks(1, 5),
    ]).then(([statsData, schedulerData, tasksData]) => {
      setStats(statsData);
      setScheduler(schedulerData);
      setRecentTasks(tasksData.items);

      // Check which niches have active tasks
      const activeNicheIds = new Set(
        tasksData.items
          .filter((t) => t.status === "queued" || t.status === "running")
          .map((t) => t.niche_id)
      );
      setRunningNiches(activeNicheIds);
      setRunningAll(false);
    });
  }, []);

  useEffect(() => {
    fetchData().finally(() => setLoading(false));
  }, [fetchData]);

  // Poll while tasks are running
  const hasRunning = runningNiches.size > 0;

  useEffect(() => {
    if (hasRunning) {
      pollRef.current = setInterval(fetchData, 4000);
    }
    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, [hasRunning, fetchData]);

  const handleStartScheduler = async () => {
    const result = await startScheduler(60);
    setScheduler(result);
  };

  const handleStopScheduler = async () => {
    const result = await stopScheduler();
    setScheduler(result);
  };

  const handleRunNow = async (nicheId?: number) => {
    if (nicheId) {
      setRunningNiches((prev) => new Set(prev).add(nicheId));
    } else {
      setRunningAll(true);
    }
    try {
      await runNow(nicheId);
      // Start polling to pick up new tasks
      setTimeout(fetchData, 1000);
    } catch {
      if (nicheId) {
        setRunningNiches((prev) => {
          const next = new Set(prev);
          next.delete(nicheId);
          return next;
        });
      } else {
        setRunningAll(false);
      }
    }
  };

  const handleToggleNiche = async (nicheId: number, enabled: boolean) => {
    const result = enabled
      ? await stopNicheSchedule(nicheId)
      : await startNicheSchedule(nicheId);

    setScheduler((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        running: prev.niches.some(
          (n) => (n.niche_id === nicheId ? result.is_enabled : n.is_enabled)
        ),
        niches: prev.niches.map((n) =>
          n.niche_id === nicheId ? result : n
        ),
      };
    });
  };

  if (loading) {
    return (
      <div className="py-8 text-center text-muted-foreground">Loading...</div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Admin Dashboard</h1>
        <p className="text-muted-foreground mt-1">
          Overview and quick actions
        </p>
      </div>

      {/* Quick Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Active Trends</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{stats.active_trends}</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Expired Trends</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{stats.expired_trends}</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Embedded</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{stats.embedded_trends}</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Researched</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{stats.researched_trends}</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Niches</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{stats.total_niches}</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Scheduler Status */}
      {scheduler && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0">
            <div className="space-y-1.5">
              <CardTitle>Scheduler</CardTitle>
              <CardDescription>
                {scheduler.running ? (
                  <span className="text-green-600">Running</span>
                ) : (
                  <span className="text-muted-foreground">Stopped</span>
                )}
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleRunNow()}
                disabled={runningAll || runningNiches.size > 0}
              >
                {runningAll ? "Triggering..." : "Run All Now"}
              </Button>
              {scheduler.running ? (
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={handleStopScheduler}
                >
                  Stop
                </Button>
              ) : (
                <Button size="sm" onClick={handleStartScheduler}>
                  Start
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {scheduler.niches.map((niche) => {
              const isRunning = runningNiches.has(niche.niche_id);
              return (
                <div
                  key={niche.niche_id}
                  className="flex items-center justify-between gap-4 rounded-lg border px-4 py-3"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{niche.niche_name}</span>
                      <span className="text-xs text-muted-foreground">
                        {niche.trend_count} active trends
                      </span>
                      {isRunning && (
                        <span className="inline-flex items-center gap-1.5 text-xs text-blue-500">
                          <span className="animate-spin rounded-full h-3 w-3 border-2 border-blue-500 border-t-transparent" />
                          Collecting...
                        </span>
                      )}
                    </div>
                    <div className="flex gap-3 text-xs text-muted-foreground mt-1">
                      <span>Every {niche.interval_minutes} min</span>
                      {niche.last_run_at && (
                        <span>
                          Last: {new Date(niche.last_run_at).toLocaleString()}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleRunNow(niche.niche_id)}
                      disabled={isRunning || runningAll}
                    >
                      {isRunning ? "Running..." : "Run"}
                    </Button>
                    <Button
                      size="sm"
                      variant={niche.is_enabled ? "default" : "outline"}
                      onClick={() =>
                        handleToggleNiche(niche.niche_id, niche.is_enabled)
                      }
                      className={
                        niche.is_enabled
                          ? "bg-green-600 hover:bg-green-700 text-white"
                          : ""
                      }
                    >
                      {niche.is_enabled ? "Enabled" : "Disabled"}
                    </Button>
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>
      )}

      {/* Recent Tasks */}
      {recentTasks.length > 0 && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0">
            <div className="space-y-1.5">
              <CardTitle>Recent Tasks</CardTitle>
              <CardDescription>
                Last {recentTasks.length} collection tasks
                {hasRunning && " \u00b7 auto-refreshing"}
              </CardDescription>
            </div>
            <Button variant="outline" size="sm" asChild>
              <Link href="/admin/tasks">View All</Link>
            </Button>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {recentTasks.map((task) => (
                <div
                  key={task.id}
                  className="flex items-center justify-between gap-4 text-sm rounded-lg border px-4 py-2"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <span
                      className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[task.status] || "bg-gray-100 text-gray-700"}`}
                    >
                      {(task.status === "queued" ||
                        task.status === "running") && (
                        <span className="relative flex h-2 w-2">
                          <span className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 bg-current" />
                          <span className="relative inline-flex rounded-full h-2 w-2 bg-current" />
                        </span>
                      )}
                      {task.status}
                    </span>
                    <span className="font-medium">{task.niche_name}</span>
                    {task.status === "completed" && (
                      <span className="text-xs text-muted-foreground">
                        {task.trends_created} trends created
                      </span>
                    )}
                    {task.error_message && (
                      <span className="text-xs text-red-500 truncate max-w-[200px]">
                        {task.error_message}
                      </span>
                    )}
                  </div>
                  <span className="text-xs text-muted-foreground whitespace-nowrap">
                    {new Date(task.started_at).toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

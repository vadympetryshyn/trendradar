"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { CircleStop, Trash2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Checkbox } from "@/components/ui/checkbox";
import {
  getCollectionTasks,
  getSchedulerStatus,
  stopCollectionTask,
  deleteCollectionTask,
  deleteCollectionTasksBulk,
  runNow,
} from "@/lib/api";
import type { CollectionTask, SchedulerStatus } from "@/lib/types";
import { STATUS_COLORS } from "@/lib/constants";

const STATUS_LABELS: Record<string, string> = {
  queued: "Queued",
  running: "Running",
  completed: "Completed",
  failed: "Failed",
  stopped: "Stopped",
};

const IN_PROGRESS = ["queued", "running"];

export default function TasksPage() {
  const [tasks, setTasks] = useState<CollectionTask[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const [stoppingId, setStoppingId] = useState<number | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [bulkDeleting, setBulkDeleting] = useState(false);
  const [scheduler, setScheduler] = useState<SchedulerStatus | null>(null);
  const [runningNiches, setRunningNiches] = useState<Set<string>>(new Set());
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const perPage = 20;

  const fetchTasks = useCallback(() => {
    return getCollectionTasks(page, perPage, statusFilter).then((data) => {
      setTasks(data.items);
      setTotal(data.total);
    });
  }, [page, statusFilter]);

  const fetchAll = useCallback(() => {
    return Promise.all([
      getCollectionTasks(page, perPage, statusFilter),
      getSchedulerStatus(),
    ]).then(([tasksData, schedulerData]) => {
      setTasks(tasksData.items);
      setTotal(tasksData.total);
      setScheduler(schedulerData);

      const activeKeys = new Set(
        tasksData.items
          .filter((t) => IN_PROGRESS.includes(t.status))
          .map((t) => `${t.niche_id}-${t.collection_type}`)
      );
      setRunningNiches(activeKeys);
    });
  }, [page, statusFilter]);

  useEffect(() => {
    setLoading(true);
    fetchAll().finally(() => setLoading(false));
  }, [fetchAll]);

  // Auto-refresh while there are in-progress tasks
  const hasInProgress = tasks.some((t) => IN_PROGRESS.includes(t.status));

  useEffect(() => {
    if (hasInProgress) {
      pollRef.current = setInterval(fetchAll, 3000);
    }
    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, [hasInProgress, fetchAll]);

  const handleStop = async (id: number) => {
    setStoppingId(id);
    try {
      await stopCollectionTask(id);
      await fetchAll();
    } catch {
      alert("Failed to stop task");
    } finally {
      setStoppingId(null);
    }
  };

  const handleDelete = async (id: number) => {
    setDeletingId(id);
    try {
      await deleteCollectionTask(id);
      setTasks((prev) => prev.filter((t) => t.id !== id));
      setTotal((prev) => prev - 1);
    } catch {
      alert("Failed to delete task");
    } finally {
      setDeletingId(null);
    }
  };

  const handleRunNiche = async (nicheId: number, collectionType: string) => {
    const key = `${nicheId}-${collectionType}`;
    setRunningNiches((prev) => new Set(prev).add(key));
    try {
      await runNow(nicheId, collectionType);
      setTimeout(fetchAll, 1000);
    } catch {
      setRunningNiches((prev) => {
        const next = new Set(prev);
        next.delete(key);
        return next;
      });
    }
  };

  const totalPages = Math.ceil(total / perPage);

  const allSelected =
    tasks.length > 0 && tasks.every((t) => selectedIds.has(t.id));

  const toggleSelectAll = () => {
    if (allSelected) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(tasks.map((t) => t.id)));
    }
  };

  const toggleSelect = (id: number) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const handleBulkDelete = async () => {
    if (selectedIds.size === 0) return;
    setBulkDeleting(true);
    try {
      await deleteCollectionTasksBulk(Array.from(selectedIds));
      setTasks((prev) => prev.filter((t) => !selectedIds.has(t.id)));
      setTotal((prev) => prev - selectedIds.size);
      setSelectedIds(new Set());
    } catch {
      alert("Failed to delete tasks");
    } finally {
      setBulkDeleting(false);
    }
  };

  if (loading && tasks.length === 0) {
    return (
      <div className="py-8 text-center text-muted-foreground">Loading...</div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Tasks</h1>
          <p className="text-muted-foreground mt-1">
            Run collection tasks and view history
          </p>
        </div>
        {selectedIds.size > 0 && (
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="destructive" disabled={bulkDeleting}>
                <Trash2 className="h-4 w-4 mr-2" />
                {bulkDeleting
                  ? "Deleting..."
                  : `Delete Selected (${selectedIds.size})`}
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>
                  Delete {selectedIds.size} task(s)
                </AlertDialogTitle>
                <AlertDialogDescription>
                  Permanently delete the selected tasks? Running tasks will be
                  stopped first.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction onClick={handleBulkDelete}>
                  Delete
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        )}
      </div>

      {/* Tasks by Niche */}
      {scheduler && (
        <Card>
          <CardHeader>
            <CardTitle>Tasks by Niche</CardTitle>
            <CardDescription>
              {scheduler.niches.length} niche{scheduler.niches.length !== 1 ? "s" : ""}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {scheduler.niches.map((niche) => {
                const nicheKey = `${niche.niche_id}-${niche.collection_type}`;
                const isRunning = runningNiches.has(nicheKey);
                return (
                  <div
                    key={`${niche.niche_id}-${niche.collection_type}`}
                    className="flex items-center justify-between gap-4 rounded-lg border px-4 py-3"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{niche.niche_name}</span>
                        <Badge variant="outline" className="text-xs">
                          {niche.collection_type}
                        </Badge>
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
                      {niche.last_run_at && (
                        <p className="text-xs text-muted-foreground mt-1">
                          Last run: {new Date(niche.last_run_at).toLocaleString()}
                        </p>
                      )}
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleRunNiche(niche.niche_id, niche.collection_type)}
                      disabled={isRunning}
                    >
                      {isRunning ? "Running..." : "Run"}
                    </Button>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Task History */}
      <div className="flex gap-2">
        {[undefined, "queued", "running", "completed", "failed", "stopped"].map(
          (s) => (
            <Badge
              key={s ?? "all"}
              variant={statusFilter === s ? "default" : "outline"}
              className="cursor-pointer"
              onClick={() => {
                setStatusFilter(s);
                setPage(1);
              }}
            >
              {s ? STATUS_LABELS[s] || s : "All"}
            </Badge>
          )
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Task History</CardTitle>
          <CardDescription>
            {total} task{total !== 1 ? "s" : ""}
            {hasInProgress && " \u00b7 auto-refreshing"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-muted-foreground">
                  <th className="pb-2 pr-4 font-medium w-10">
                    <Checkbox
                      checked={allSelected}
                      onCheckedChange={toggleSelectAll}
                    />
                  </th>
                  <th className="pb-2 pr-4 font-medium w-10">#</th>
                  <th className="pb-2 pr-4 font-medium">Niche</th>
                  <th className="pb-2 pr-4 font-medium">Status</th>
                  <th className="pb-2 pr-4 font-medium text-right">
                    Created
                  </th>
                  <th className="pb-2 pr-4 font-medium text-right">
                    Expired
                  </th>
                  <th className="pb-2 pr-4 font-medium">Error</th>
                  <th className="pb-2 pr-4 font-medium">Started</th>
                  <th className="pb-2 pr-4 font-medium">Completed</th>
                  <th className="pb-2 font-medium w-20" />
                </tr>
              </thead>
              <tbody>
                {tasks.map((task) => {
                  const isActive = IN_PROGRESS.includes(task.status);
                  return (
                    <tr
                      key={task.id}
                      className={`border-b last:border-0 ${selectedIds.has(task.id) ? "bg-muted/30" : ""}`}
                    >
                      <td className="py-3 pr-4">
                        <Checkbox
                          checked={selectedIds.has(task.id)}
                          onCheckedChange={() => toggleSelect(task.id)}
                        />
                      </td>
                      <td className="py-3 pr-4 text-muted-foreground tabular-nums">
                        {task.id}
                      </td>
                      <td className="py-3 pr-4 font-medium">
                        {task.niche_name}
                      </td>
                      <td className="py-3 pr-4">
                        <span
                          className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_COLORS[task.status] || "bg-gray-100 text-gray-700"}`}
                        >
                          {isActive && (
                            <span className="relative flex h-2 w-2">
                              <span className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 bg-current" />
                              <span className="relative inline-flex rounded-full h-2 w-2 bg-current" />
                            </span>
                          )}
                          {STATUS_LABELS[task.status] || task.status}
                        </span>
                      </td>
                      <td className="py-3 pr-4 text-right tabular-nums">
                        {task.trends_created}
                      </td>
                      <td className="py-3 pr-4 text-right tabular-nums">
                        {task.trends_expired}
                      </td>
                      <td className="py-3 pr-4 max-w-[200px] truncate text-red-500">
                        {task.error_message || "\u2014"}
                      </td>
                      <td className="py-3 pr-4 text-muted-foreground whitespace-nowrap">
                        {new Date(task.started_at).toLocaleString()}
                      </td>
                      <td className="py-3 pr-4 text-muted-foreground whitespace-nowrap">
                        {task.completed_at
                          ? new Date(task.completed_at).toLocaleString()
                          : "\u2014"}
                      </td>
                      <td className="py-3">
                        <div className="flex gap-1">
                          {isActive && (
                            <Button
                              size="icon"
                              variant="ghost"
                              disabled={stoppingId === task.id}
                              onClick={() => handleStop(task.id)}
                              className="h-7 w-7 text-muted-foreground hover:text-orange-600"
                              title="Stop task"
                            >
                              <CircleStop className="h-3.5 w-3.5" />
                            </Button>
                          )}
                          <AlertDialog>
                            <AlertDialogTrigger asChild>
                              <Button
                                size="icon"
                                variant="ghost"
                                disabled={deletingId === task.id}
                                className="h-7 w-7 text-muted-foreground hover:text-destructive"
                                title="Delete task"
                              >
                                <Trash2 className="h-3.5 w-3.5" />
                              </Button>
                            </AlertDialogTrigger>
                            <AlertDialogContent>
                              <AlertDialogHeader>
                                <AlertDialogTitle>
                                  Delete task
                                </AlertDialogTitle>
                                <AlertDialogDescription>
                                  Permanently delete this task record? If the
                                  task is running, it will be stopped first.
                                </AlertDialogDescription>
                              </AlertDialogHeader>
                              <AlertDialogFooter>
                                <AlertDialogCancel>Cancel</AlertDialogCancel>
                                <AlertDialogAction
                                  onClick={() => handleDelete(task.id)}
                                >
                                  Delete
                                </AlertDialogAction>
                              </AlertDialogFooter>
                            </AlertDialogContent>
                          </AlertDialog>
                        </div>
                      </td>
                    </tr>
                  );
                })}
                {tasks.length === 0 && (
                  <tr>
                    <td
                      colSpan={10}
                      className="py-8 text-center text-muted-foreground"
                    >
                      No tasks found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-between pt-4">
              <p className="text-sm text-muted-foreground">
                Page {page} of {totalPages}
              </p>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => p - 1)}
                >
                  Previous
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

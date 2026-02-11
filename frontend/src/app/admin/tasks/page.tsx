"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Square, Trash2 } from "lucide-react";
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
import {
  getTasks,
  deleteTask,
  triggerAllAnalyses,
  stopTask,
  stopAllTasks,
} from "@/lib/api";
import type { TaskListItem } from "@/lib/types";
import { StatusBadge } from "../_components/status-badge";

const IN_PROGRESS_STATUSES = ["pending", "queued", "fetching", "analyzing"];

export default function TasksPage() {
  const [items, setItems] = useState<TaskListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [stoppingId, setStoppingId] = useState<string | null>(null);
  const [runningAll, setRunningAll] = useState(false);
  const [stoppingAll, setStoppingAll] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const perPage = 20;

  const fetchData = useCallback(() => {
    return getTasks(page, perPage).then((data) => {
      setItems(data.items);
      setTotal(data.total);
    });
  }, [page]);

  useEffect(() => {
    setLoading(true);
    fetchData().finally(() => setLoading(false));
  }, [fetchData]);

  // Auto-refresh while there are in-progress tasks
  const hasInProgress = items.some((i) =>
    IN_PROGRESS_STATUSES.includes(i.status)
  );

  useEffect(() => {
    if (hasInProgress) {
      pollRef.current = setInterval(() => {
        fetchData();
      }, 3000);
    }
    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, [hasInProgress, fetchData]);

  const handleDelete = async (id: number) => {
    setDeletingId(id);
    try {
      await deleteTask(id);
      setItems((prev) => prev.filter((item) => item.id !== id));
      setTotal((prev) => prev - 1);
    } catch {
      alert("Failed to delete task");
    } finally {
      setDeletingId(null);
    }
  };

  const handleStop = async (celeryTaskId: string) => {
    setStoppingId(celeryTaskId);
    try {
      await stopTask(celeryTaskId);
      await fetchData();
    } catch {
      alert("Failed to stop task");
    } finally {
      setStoppingId(null);
    }
  };

  const handleRunAll = async () => {
    setRunningAll(true);
    try {
      await triggerAllAnalyses();
      await fetchData();
    } catch {
      alert("Failed to trigger analyses");
    } finally {
      setRunningAll(false);
    }
  };

  const handleStopAll = async () => {
    setStoppingAll(true);
    try {
      await stopAllTasks();
      await fetchData();
    } catch {
      alert("Failed to stop tasks");
    } finally {
      setStoppingAll(false);
    }
  };

  const totalPages = Math.ceil(total / perPage);

  if (loading && items.length === 0) {
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
            All analysis tasks with statuses
          </p>
        </div>
        <div className="flex gap-2">
          {hasInProgress && (
            <Button
              variant="destructive"
              onClick={handleStopAll}
              disabled={stoppingAll}
            >
              {stoppingAll ? "Stopping..." : "Stop All"}
            </Button>
          )}
          <Button onClick={handleRunAll} disabled={runningAll}>
            {runningAll ? "Starting..." : "Run All"}
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Analysis Tasks</CardTitle>
          <CardDescription>
            {total} total task{total === 1 ? "" : "s"}
            {hasInProgress && " · auto-refreshing"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-muted-foreground">
                  <th className="pb-2 pr-4 font-medium w-10">#</th>
                  <th className="pb-2 pr-4 font-medium">Task ID</th>
                  <th className="pb-2 pr-4 font-medium">Niche</th>
                  <th className="pb-2 pr-4 font-medium">Status</th>
                  <th className="pb-2 pr-4 font-medium text-right">Posts</th>
                  <th className="pb-2 pr-4 font-medium text-right">
                    Subreddits
                  </th>
                  <th className="pb-2 pr-4 font-medium">Error</th>
                  <th className="pb-2 pr-4 font-medium">Started</th>
                  <th className="pb-2 pr-4 font-medium">Completed</th>
                  <th className="pb-2 font-medium w-20" />
                </tr>
              </thead>
              <tbody>
                {items.map((item, index) => {
                  const isInProgress = IN_PROGRESS_STATUSES.includes(
                    item.status
                  );

                  return (
                    <tr key={item.id} className="border-b last:border-0">
                      <td className="py-3 pr-4 text-muted-foreground tabular-nums">
                        {(page - 1) * perPage + index + 1}
                      </td>
                      <td className="py-3 pr-4 font-mono text-xs">
                        {item.celery_task_id
                          ? item.celery_task_id.slice(0, 8)
                          : "—"}
                      </td>
                      <td className="py-3 pr-4 font-medium">
                        {item.niche_name}
                      </td>
                      <td className="py-3 pr-4">
                        <StatusBadge status={item.status} />
                      </td>
                      <td className="py-3 pr-4 text-right tabular-nums">
                        {item.posts_fetched}
                      </td>
                      <td className="py-3 pr-4 text-right tabular-nums">
                        {item.subreddits_fetched}
                      </td>
                      <td className="py-3 pr-4 max-w-[200px] truncate text-red-500">
                        {item.error_message || "—"}
                      </td>
                      <td className="py-3 pr-4 text-muted-foreground">
                        {item.started_at
                          ? new Date(item.started_at).toLocaleString()
                          : "—"}
                      </td>
                      <td className="py-3 pr-4 text-muted-foreground">
                        {item.completed_at
                          ? new Date(item.completed_at).toLocaleString()
                          : "—"}
                      </td>
                      <td className="py-3">
                        <div className="flex gap-1">
                          {isInProgress && item.celery_task_id && (
                            <Button
                              size="icon-xs"
                              variant="ghost"
                              disabled={stoppingId === item.celery_task_id}
                              onClick={() =>
                                handleStop(item.celery_task_id!)
                              }
                              className="text-muted-foreground hover:text-orange-600"
                              title="Stop task"
                            >
                              <Square />
                            </Button>
                          )}
                          <AlertDialog>
                            <AlertDialogTrigger asChild>
                              <Button
                                size="icon-xs"
                                variant="ghost"
                                disabled={deletingId === item.id}
                                className="text-muted-foreground hover:text-destructive"
                                title="Delete task"
                              >
                                <Trash2 />
                              </Button>
                            </AlertDialogTrigger>
                            <AlertDialogContent>
                              <AlertDialogHeader>
                                <AlertDialogTitle>
                                  Delete task
                                </AlertDialogTitle>
                                <AlertDialogDescription>
                                  This will permanently delete this task and its
                                  associated analysis data. This action cannot be
                                  undone.
                                </AlertDialogDescription>
                              </AlertDialogHeader>
                              <AlertDialogFooter>
                                <AlertDialogCancel>Cancel</AlertDialogCancel>
                                <AlertDialogAction
                                  variant="destructive"
                                  onClick={() => handleDelete(item.id)}
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
                {items.length === 0 && (
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

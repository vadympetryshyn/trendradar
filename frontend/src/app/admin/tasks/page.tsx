"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Square, Trash2 } from "lucide-react";
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
import {
  getCollectionTasks,
  stopCollectionTask,
  deleteCollectionTask,
  runNow,
} from "@/lib/api";
import type { CollectionTask } from "@/lib/types";

const STATUS_COLORS: Record<string, string> = {
  queued: "bg-gray-100 text-gray-700",
  running: "bg-blue-100 text-blue-700",
  completed: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
  stopped: "bg-yellow-100 text-yellow-700",
};

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
  const [triggeringAll, setTriggeringAll] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const perPage = 20;

  const fetchTasks = useCallback(() => {
    return getCollectionTasks(page, perPage, statusFilter).then((data) => {
      setTasks(data.items);
      setTotal(data.total);
    });
  }, [page, statusFilter]);

  useEffect(() => {
    setLoading(true);
    fetchTasks().finally(() => setLoading(false));
  }, [fetchTasks]);

  // Auto-refresh while there are in-progress tasks
  const hasInProgress = tasks.some((t) => IN_PROGRESS.includes(t.status));

  useEffect(() => {
    if (hasInProgress) {
      pollRef.current = setInterval(fetchTasks, 3000);
    }
    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, [hasInProgress, fetchTasks]);

  const handleStop = async (id: number) => {
    setStoppingId(id);
    try {
      await stopCollectionTask(id);
      await fetchTasks();
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

  const handleRunAll = async () => {
    setTriggeringAll(true);
    try {
      await runNow();
      await fetchTasks();
    } catch {
      alert("Failed to trigger collection");
    } finally {
      setTriggeringAll(false);
    }
  };

  const totalPages = Math.ceil(total / perPage);

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
            Collection task history and status
          </p>
        </div>
        <Button onClick={handleRunAll} disabled={triggeringAll}>
          {triggeringAll ? "Triggering..." : "Run Now"}
        </Button>
      </div>

      {/* Status filter */}
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
          <CardTitle>Collection Tasks</CardTitle>
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
                {tasks.map((task, index) => {
                  const isActive = IN_PROGRESS.includes(task.status);
                  return (
                    <tr key={task.id} className="border-b last:border-0">
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
                              <Square className="h-3.5 w-3.5" />
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
                      colSpan={9}
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

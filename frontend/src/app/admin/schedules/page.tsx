"use client";

import { useEffect, useState } from "react";
import { Plus, Trash2 } from "lucide-react";
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  getNiches,
  getSchedules,
  createSchedule,
  updateSchedule,
  deleteSchedule,
} from "@/lib/api";
import type { Niche, ScheduleConfig } from "@/lib/types";

export default function SchedulesPage() {
  const [schedules, setSchedules] = useState<ScheduleConfig[]>([]);
  const [niches, setNiches] = useState<Niche[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [createNicheId, setCreateNicheId] = useState<string>("");
  const [createInterval, setCreateInterval] = useState(60);
  const [creating, setCreating] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  useEffect(() => {
    Promise.all([getSchedules(), getNiches()])
      .then(([schedulesData, nichesData]) => {
        setSchedules(schedulesData);
        setNiches(nichesData);
      })
      .finally(() => setLoading(false));
  }, []);

  const handleToggle = async (schedule: ScheduleConfig) => {
    try {
      const updated = await updateSchedule(schedule.id, {
        is_enabled: !schedule.is_enabled,
      });
      setSchedules((prev) =>
        prev.map((s) => (s.id === updated.id ? updated : s))
      );
    } catch {
      alert("Failed to update schedule");
    }
  };

  const handleIntervalChange = async (
    schedule: ScheduleConfig,
    value: number
  ) => {
    if (value < 15 || value > 1440) return;
    try {
      const updated = await updateSchedule(schedule.id, {
        interval_minutes: value,
      });
      setSchedules((prev) =>
        prev.map((s) => (s.id === updated.id ? updated : s))
      );
    } catch {
      alert("Failed to update interval");
    }
  };

  const handleCreate = async () => {
    if (!createNicheId) return;
    setCreating(true);
    try {
      const created = await createSchedule({
        niche_id: parseInt(createNicheId),
        interval_minutes: createInterval,
        is_enabled: true,
      });
      setSchedules((prev) => [...prev, created]);
      setShowCreate(false);
      setCreateNicheId("");
      setCreateInterval(60);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to create schedule");
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: number) => {
    setDeletingId(id);
    try {
      await deleteSchedule(id);
      setSchedules((prev) => prev.filter((s) => s.id !== id));
    } catch {
      alert("Failed to delete schedule");
    } finally {
      setDeletingId(null);
    }
  };

  if (loading) {
    return (
      <div className="py-8 text-center text-muted-foreground">Loading...</div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Schedules</h1>
          <p className="text-muted-foreground mt-1">
            Manage automated analysis schedules
          </p>
        </div>
        <Button onClick={() => setShowCreate(true)} disabled={showCreate}>
          <Plus /> Create Schedule
        </Button>
      </div>

      {showCreate && (
        <Card>
          <CardHeader>
            <CardTitle>Create Schedule</CardTitle>
            <CardDescription>
              Set up automatic analysis for a niche
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-end gap-4">
              <div className="space-y-1.5">
                <label className="text-sm font-medium">Niche</label>
                <Select value={createNicheId} onValueChange={setCreateNicheId}>
                  <SelectTrigger className="w-[200px]">
                    <SelectValue placeholder="Select a niche" />
                  </SelectTrigger>
                  <SelectContent>
                    {niches.map((n) => (
                      <SelectItem key={n.id} value={String(n.id)}>
                        {n.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium">
                  Interval (minutes)
                </label>
                <input
                  type="number"
                  min={15}
                  max={1440}
                  value={createInterval}
                  onChange={(e) => setCreateInterval(parseInt(e.target.value))}
                  className="h-9 w-24 rounded-md border bg-background px-3 text-sm"
                />
              </div>
              <Button
                onClick={handleCreate}
                disabled={!createNicheId || creating}
              >
                {creating ? "Creating..." : "Create"}
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  setShowCreate(false);
                  setCreateNicheId("");
                  setCreateInterval(60);
                }}
              >
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Scheduled Jobs</CardTitle>
          <CardDescription>
            {schedules.length} schedule{schedules.length === 1 ? "" : "s"}{" "}
            configured &middot;{" "}
            {schedules.filter((s) => s.is_enabled).length} active
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-muted-foreground">
                  <th className="pb-2 pr-4 font-medium">Niche</th>
                  <th className="pb-2 pr-4 font-medium">Status</th>
                  <th className="pb-2 pr-4 font-medium">Interval</th>
                  <th className="pb-2 pr-4 font-medium">Last Run</th>
                  <th className="pb-2 pr-4 font-medium">Next Run</th>
                  <th className="pb-2 font-medium w-10" />
                </tr>
              </thead>
              <tbody>
                {schedules.map((schedule) => (
                  <tr key={schedule.id} className="border-b last:border-0">
                    <td className="py-3 pr-4 font-medium">
                      {schedule.niche_name || `Niche #${schedule.niche_id}`}
                    </td>
                    <td className="py-3 pr-4">
                      <Button
                        size="xs"
                        variant={schedule.is_enabled ? "default" : "outline"}
                        onClick={() => handleToggle(schedule)}
                        className={
                          schedule.is_enabled
                            ? "bg-green-600 hover:bg-green-700 text-white"
                            : ""
                        }
                      >
                        {schedule.is_enabled ? "Enabled" : "Disabled"}
                      </Button>
                    </td>
                    <td className="py-3 pr-4">
                      <div className="flex items-center gap-1.5">
                        <span className="text-muted-foreground">Every</span>
                        <input
                          type="number"
                          min={15}
                          max={1440}
                          value={schedule.interval_minutes}
                          onChange={(e) => {
                            const val = parseInt(e.target.value);
                            if (val >= 15 && val <= 1440) {
                              handleIntervalChange(schedule, val);
                            }
                          }}
                          className="w-16 rounded-md border bg-background px-2 py-1 text-sm tabular-nums"
                        />
                        <span className="text-muted-foreground">min</span>
                      </div>
                    </td>
                    <td className="py-3 pr-4 text-muted-foreground">
                      {schedule.last_run_at
                        ? new Date(schedule.last_run_at).toLocaleString()
                        : "Never"}
                    </td>
                    <td className="py-3 pr-4 text-muted-foreground">
                      {schedule.is_enabled && schedule.next_run_at
                        ? new Date(schedule.next_run_at).toLocaleString()
                        : "—"}
                    </td>
                    <td className="py-3">
                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <Button
                            size="icon-xs"
                            variant="ghost"
                            disabled={deletingId === schedule.id}
                            className="text-muted-foreground hover:text-destructive"
                          >
                            <Trash2 />
                          </Button>
                        </AlertDialogTrigger>
                        <AlertDialogContent>
                          <AlertDialogHeader>
                            <AlertDialogTitle>
                              Delete schedule
                            </AlertDialogTitle>
                            <AlertDialogDescription>
                              This will permanently delete this schedule for{" "}
                              <strong>{schedule.niche_name}</strong>. Automatic
                              analysis will stop.
                            </AlertDialogDescription>
                          </AlertDialogHeader>
                          <AlertDialogFooter>
                            <AlertDialogCancel>Cancel</AlertDialogCancel>
                            <AlertDialogAction
                              variant="destructive"
                              onClick={() => handleDelete(schedule.id)}
                            >
                              Delete
                            </AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                    </td>
                  </tr>
                ))}
                {schedules.length === 0 && (
                  <tr>
                    <td
                      colSpan={6}
                      className="py-8 text-center text-muted-foreground"
                    >
                      No schedules configured. Create one to get started.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

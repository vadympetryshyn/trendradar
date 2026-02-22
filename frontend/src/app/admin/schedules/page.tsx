"use client";

import { useEffect, useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  getSchedulerStatus,
  startScheduler,
  stopScheduler,
  startNicheSchedule,
  stopNicheSchedule,
  runNow,
} from "@/lib/api";
import type { SchedulerStatus } from "@/lib/types";

const INTERVAL_OPTIONS = [
  { label: "15 min", value: 15 },
  { label: "30 min", value: 30 },
  { label: "1 hour", value: 60 },
  { label: "2 hours", value: 120 },
  { label: "5 hours", value: 300 },
  { label: "12 hours", value: 720 },
  { label: "24 hours", value: 1440 },
];

export default function SchedulerPage() {
  const [scheduler, setScheduler] = useState<SchedulerStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedInterval, setSelectedInterval] = useState("60");
  const [runningNiche, setRunningNiche] = useState<number | null>(null);

  useEffect(() => {
    getSchedulerStatus()
      .then(setScheduler)
      .finally(() => setLoading(false));
  }, []);

  const handleStart = async () => {
    const result = await startScheduler(parseInt(selectedInterval));
    setScheduler(result);
  };

  const handleStop = async () => {
    const result = await stopScheduler();
    setScheduler(result);
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

  const handleRunNiche = async (nicheId: number) => {
    setRunningNiche(nicheId);
    try {
      await runNow(nicheId);
    } finally {
      setRunningNiche(null);
    }
  };

  if (loading) {
    return (
      <div className="py-8 text-center text-muted-foreground">Loading...</div>
    );
  }

  if (!scheduler) {
    return (
      <div className="py-8 text-center text-muted-foreground">
        Failed to load scheduler status
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Scheduler</h1>
        <p className="text-muted-foreground mt-1">
          Manage automated trend collection
        </p>
      </div>

      {/* Global Scheduler Control */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <div className="space-y-1.5">
            <CardTitle>Scheduler Control</CardTitle>
            <CardDescription>
              Status:{" "}
              {scheduler.running ? (
                <span className="text-green-600 font-medium">Running</span>
              ) : (
                <span className="text-muted-foreground font-medium">
                  Stopped
                </span>
              )}
            </CardDescription>
          </div>
          <div className="flex items-center gap-3">
            <Select
              value={selectedInterval}
              onValueChange={setSelectedInterval}
            >
              <SelectTrigger className="w-[140px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {INTERVAL_OPTIONS.map((opt) => (
                  <SelectItem key={opt.value} value={String(opt.value)}>
                    {opt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {scheduler.running ? (
              <Button variant="destructive" onClick={handleStop}>
                Stop All
              </Button>
            ) : (
              <Button onClick={handleStart}>Start All</Button>
            )}
          </div>
        </CardHeader>
      </Card>

      {/* Per-Niche Controls */}
      <Card>
        <CardHeader>
          <CardTitle>Per-Niche Schedules</CardTitle>
          <CardDescription>
            {scheduler.niches.filter((n) => n.is_enabled).length} of{" "}
            {scheduler.niches.length} enabled
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
                  <th className="pb-2 pr-4 font-medium text-right">
                    Active Trends
                  </th>
                  <th className="pb-2 pr-4 font-medium">Last Run</th>
                  <th className="pb-2 pr-4 font-medium">Next Run</th>
                  <th className="pb-2 font-medium" />
                </tr>
              </thead>
              <tbody>
                {scheduler.niches.map((niche) => (
                  <tr key={niche.niche_id} className="border-b last:border-0">
                    <td className="py-3 pr-4 font-medium">
                      {niche.niche_name}
                    </td>
                    <td className="py-3 pr-4">
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
                    </td>
                    <td className="py-3 pr-4 text-muted-foreground">
                      Every {niche.interval_minutes} min
                    </td>
                    <td className="py-3 pr-4 text-right tabular-nums">
                      {niche.trend_count}
                    </td>
                    <td className="py-3 pr-4 text-muted-foreground">
                      {niche.last_run_at
                        ? new Date(niche.last_run_at).toLocaleString()
                        : "Never"}
                    </td>
                    <td className="py-3 pr-4 text-muted-foreground">
                      {niche.is_enabled && niche.next_run_at
                        ? new Date(niche.next_run_at).toLocaleString()
                        : "—"}
                    </td>
                    <td className="py-3">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleRunNiche(niche.niche_id)}
                        disabled={runningNiche === niche.niche_id}
                      >
                        {runningNiche === niche.niche_id
                          ? "Running..."
                          : "Run Now"}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

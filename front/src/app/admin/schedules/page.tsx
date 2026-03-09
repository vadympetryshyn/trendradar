"use client";

import { useEffect, useState } from "react";
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
  updateNicheInterval,
} from "@/lib/api";
import type { SchedulerStatus } from "@/lib/types";

const TYPE_ORDER: Record<string, number> = {
  now: 0,
  daily: 1,
  weekly: 2,
  rising: 3,
};

const TYPE_FILTER_OPTIONS = [
  { label: "All Types", value: "all" },
  { label: "Now", value: "now" },
  { label: "Daily", value: "daily" },
  { label: "Weekly", value: "weekly" },
  { label: "Rising", value: "rising" },
];

const INTERVAL_OPTIONS = [
  { label: "15 min", value: 15 },
  { label: "30 min", value: 30 },
  { label: "1 hour", value: 60 },
  { label: "2 hours", value: 120 },
  { label: "4 hours", value: 240 },
  { label: "6 hours", value: 360 },
  { label: "8 hours", value: 480 },
  { label: "12 hours", value: 720 },
  { label: "24 hours", value: 1440 },
];

export default function SchedulerPage() {
  const [scheduler, setScheduler] = useState<SchedulerStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [typeFilter, setTypeFilter] = useState("all");

  useEffect(() => {
    getSchedulerStatus()
      .then(setScheduler)
      .finally(() => setLoading(false));
  }, []);

  const handleStart = async () => {
    const result = await startScheduler();
    setScheduler(result);
  };

  const handleStop = async () => {
    const result = await stopScheduler();
    setScheduler(result);
  };

  const handleToggleNiche = async (nicheId: number, collectionType: string, enabled: boolean) => {
    const result = enabled
      ? await stopNicheSchedule(nicheId, collectionType)
      : await startNicheSchedule(nicheId, collectionType);

    setScheduler((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        running: prev.niches.some(
          (n) => (n.niche_id === nicheId && n.collection_type === collectionType ? result.is_enabled : n.is_enabled)
        ),
        niches: prev.niches.map((n) =>
          n.niche_id === nicheId && n.collection_type === collectionType ? result : n
        ),
      };
    });
  };

  const handleIntervalChange = async (nicheId: number, collectionType: string, intervalMinutes: number) => {
    const result = await updateNicheInterval(nicheId, collectionType, intervalMinutes);
    setScheduler((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        niches: prev.niches.map((n) =>
          n.niche_id === nicheId && n.collection_type === collectionType ? result : n
        ),
      };
    });
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
            <Button onClick={handleStart}>Enable All</Button>
            <Button variant="destructive" onClick={handleStop}>
              Disable All
            </Button>
          </div>
        </CardHeader>
      </Card>

      {/* Per-Niche Controls */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <div className="space-y-1.5">
            <CardTitle>Per-Niche Schedules</CardTitle>
            <CardDescription>
              {scheduler.niches.filter((n) => n.is_enabled).length} of{" "}
              {scheduler.niches.length} enabled
            </CardDescription>
          </div>
          <Select value={typeFilter} onValueChange={setTypeFilter}>
            <SelectTrigger className="w-[140px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {TYPE_FILTER_OPTIONS.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-muted-foreground">
                  <th className="pb-2 pr-4 font-medium">Niche</th>
                  <th className="pb-2 pr-4 font-medium">Type</th>
                  <th className="pb-2 pr-4 font-medium">Status</th>
                  <th className="pb-2 pr-4 font-medium">Interval</th>
                  <th className="pb-2 pr-4 font-medium text-right">
                    Active Trends
                  </th>
                  <th className="pb-2 pr-4 font-medium">Last Run</th>
                  <th className="pb-2 pr-4 font-medium">Next Run</th>
                </tr>
              </thead>
              <tbody>
                {scheduler.niches
                  .filter((n) => typeFilter === "all" || n.collection_type === typeFilter)
                  .sort((a, b) => (TYPE_ORDER[a.collection_type] ?? 99) - (TYPE_ORDER[b.collection_type] ?? 99))
                  .map((niche) => {
                  const nicheKey = `${niche.niche_id}-${niche.collection_type}`;
                  return (
                    <tr key={nicheKey} className="border-b last:border-0">
                      <td className="py-3 pr-4 font-medium">
                        {niche.niche_name}
                      </td>
                      <td className="py-3 pr-4">
                        <Badge variant="outline" className="text-xs">
                          {niche.collection_type}
                        </Badge>
                      </td>
                      <td className="py-3 pr-4">
                        <Button
                          size="sm"
                          variant={niche.is_enabled ? "default" : "outline"}
                          onClick={() =>
                            handleToggleNiche(niche.niche_id, niche.collection_type, niche.is_enabled)
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
                      <td className="py-3 pr-4">
                        <Select
                          value={String(niche.interval_minutes)}
                          onValueChange={(val) =>
                            handleIntervalChange(niche.niche_id, niche.collection_type, parseInt(val))
                          }
                        >
                          <SelectTrigger className="w-[120px]">
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
                          : "\u2014"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

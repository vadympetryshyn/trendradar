"use client";

import { TrendCard } from "./trend-card";
import type { Trend } from "@/lib/types";

interface TrendsGridProps {
  trends: Trend[];
}

export function TrendsGrid({ trends }: TrendsGridProps) {
  if (trends.length === 0) {
    return (
      <div className="text-center py-16 text-muted-foreground">
        No trends found.
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {trends.map((trend) => (
        <TrendCard key={trend.id} trend={trend} />
      ))}
    </div>
  );
}

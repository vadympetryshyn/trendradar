"use client";

import { TrendCard } from "./trend-card";
import type { TrendAnalysis } from "@/lib/types";
import { Separator } from "@/components/ui/separator";

interface TrendsGridProps {
  analysis: TrendAnalysis;
}

export function TrendsGrid({ analysis }: TrendsGridProps) {
  return (
    <div className="space-y-6">
      {analysis.overall_summary && (
        <div className="rounded-lg border bg-card p-4">
          <h3 className="font-semibold mb-2">Overview</h3>
          <p className="text-sm text-muted-foreground leading-relaxed">
            {analysis.overall_summary}
          </p>
          <Separator className="my-3" />
          <div className="flex gap-4 text-xs text-muted-foreground">
            <span>{analysis.posts_fetched} posts analyzed</span>
            <span>{analysis.subreddits_fetched} subreddits</span>
            <span>{analysis.trend_items.length} trends identified</span>
            {analysis.completed_at && (
              <span>
                {new Date(analysis.completed_at).toLocaleString()}
              </span>
            )}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {analysis.trend_items.map((item) => (
          <TrendCard key={item.id} item={item} />
        ))}
      </div>
    </div>
  );
}

"use client";

import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { Trend } from "@/lib/types";

const sentimentColors: Record<string, string> = {
  positive: "bg-green-100 text-green-800 border-green-200",
  negative: "bg-red-100 text-red-800 border-red-200",
  neutral: "bg-gray-100 text-gray-800 border-gray-200",
  mixed: "bg-yellow-100 text-yellow-800 border-yellow-200",
};

interface TrendCardProps {
  trend: Trend;
}

export function TrendCard({ trend }: TrendCardProps) {
  return (
    <Link href={`/admin/trends/${trend.id}`}>
      <Card className="h-full hover:bg-muted/30 transition-colors cursor-pointer">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between gap-2">
            <CardTitle className="text-lg leading-tight">{trend.title}</CardTitle>
            <span className="text-sm font-medium text-muted-foreground whitespace-nowrap">
              {Math.round(trend.relevance_score * 100)}%
            </span>
          </div>
          <div className="flex flex-wrap gap-2 pt-1">
            <Badge
              variant="outline"
              className={
                trend.trend_type === "rising"
                  ? "bg-orange-100 text-orange-800 border-orange-200"
                  : "bg-blue-100 text-blue-800 border-blue-200"
              }
            >
              {trend.trend_type}
            </Badge>
            <Badge
              variant="outline"
              className={sentimentColors[trend.sentiment] || sentimentColors.neutral}
            >
              {trend.sentiment}
            </Badge>
            <Badge variant="secondary">{trend.category}</Badge>
            {trend.mention_count > 0 && (
              <Badge variant="outline">
                {trend.mention_count} mention{trend.mention_count !== 1 ? "s" : ""}
              </Badge>
            )}
            {trend.research_done && (
              <Badge variant="outline" className="bg-purple-100 text-purple-800 border-purple-200">
                Researched
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          <CardDescription className="text-sm leading-relaxed">
            {trend.summary}
          </CardDescription>

          {trend.key_points.length > 0 && (
            <ul className="space-y-1 text-sm text-muted-foreground">
              {trend.key_points.map((point, i) => (
                <li key={i} className="flex gap-2">
                  <span className="text-primary mt-0.5">&#8226;</span>
                  <span>{point}</span>
                </li>
              ))}
            </ul>
          )}

          {trend.source_subreddits.length > 0 && (
            <div className="flex flex-wrap gap-1 pt-1">
              {trend.source_subreddits.map((sub) => (
                <span
                  key={sub}
                  className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded-full"
                >
                  r/{sub}
                </span>
              ))}
            </div>
          )}

          <p className="text-xs text-muted-foreground pt-1">
            {new Date(trend.collected_at).toLocaleString()}
          </p>
        </CardContent>
      </Card>
    </Link>
  );
}

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
import { SENTIMENT_COLORS } from "@/lib/constants";
import { stripSubredditPrefix } from "@/lib/format";
import type { Trend } from "@/lib/types";

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
              className={SENTIMENT_COLORS[trend.sentiment] || SENTIMENT_COLORS.neutral}
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
              {trend.key_points.map((point) => (
                <li key={point} className="flex gap-2">
                  <span className="text-primary mt-0.5">&#8226;</span>
                  <span>{point}</span>
                </li>
              ))}
            </ul>
          )}

          {trend.source_subreddits.length > 0 && (
            <div className="flex flex-wrap gap-1 pt-1">
              {trend.source_subreddits.map((sub) => {
                const name = stripSubredditPrefix(sub);
                return (
                  <span
                    key={sub}
                    role="link"
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      window.open(`https://www.reddit.com/r/${name}/`, "_blank", "noopener,noreferrer");
                    }}
                    className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded-full hover:text-foreground hover:bg-muted/80 transition-colors cursor-pointer"
                  >
                    r/{name}
                  </span>
                );
              })}
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

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
import { COLLECTION_TYPE_STYLES, SENTIMENT_COLORS } from "@/lib/constants";
import { stripSubredditPrefix } from "@/lib/format";
import type { Trend } from "@/lib/types";

interface TrendCardProps {
  trend: Trend;
}

export function TrendCard({ trend }: TrendCardProps) {
  return (
    <Link href={`/trends/${trend.id}`}>
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
            {COLLECTION_TYPE_STYLES[trend.collection_type] && (
              <Badge
                variant="outline"
                className={COLLECTION_TYPE_STYLES[trend.collection_type].className}
              >
                {COLLECTION_TYPE_STYLES[trend.collection_type].label}
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

"use client";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { TrendItem } from "@/lib/types";

const sentimentColors: Record<string, string> = {
  positive: "bg-green-100 text-green-800 border-green-200",
  negative: "bg-red-100 text-red-800 border-red-200",
  neutral: "bg-gray-100 text-gray-800 border-gray-200",
  mixed: "bg-yellow-100 text-yellow-800 border-yellow-200",
};

interface TrendCardProps {
  item: TrendItem;
}

export function TrendCard({ item }: TrendCardProps) {
  return (
    <Card className="h-full">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-lg leading-tight">{item.title}</CardTitle>
          <span className="text-sm font-medium text-muted-foreground whitespace-nowrap">
            {Math.round(item.relevance_score * 100)}%
          </span>
        </div>
        <div className="flex flex-wrap gap-2 pt-1">
          <Badge
            variant="outline"
            className={sentimentColors[item.sentiment] || sentimentColors.neutral}
          >
            {item.sentiment}
          </Badge>
          <Badge variant="secondary">{item.category}</Badge>
          {item.mention_count > 0 && (
            <Badge variant="outline">
              {item.mention_count} mention{item.mention_count !== 1 ? "s" : ""}
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <CardDescription className="text-sm leading-relaxed">
          {item.summary}
        </CardDescription>

        {item.key_points.length > 0 && (
          <ul className="space-y-1 text-sm text-muted-foreground">
            {item.key_points.map((point, i) => (
              <li key={i} className="flex gap-2">
                <span className="text-primary mt-0.5">&#8226;</span>
                <span>{point}</span>
              </li>
            ))}
          </ul>
        )}

        {item.source_subreddits.length > 0 && (
          <div className="flex flex-wrap gap-1 pt-1">
            {item.source_subreddits.map((sub) => (
              <span
                key={sub}
                className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded-full"
              >
                r/{sub}
              </span>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

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
import type { TrendSearchResult } from "@/lib/types";

const sentimentColors: Record<string, string> = {
  positive: "bg-green-100 text-green-800 border-green-200",
  negative: "bg-red-100 text-red-800 border-red-200",
  neutral: "bg-gray-100 text-gray-800 border-gray-200",
  mixed: "bg-yellow-100 text-yellow-800 border-yellow-200",
};

interface SearchResultCardProps {
  result: TrendSearchResult;
}

export function SearchResultCard({ result }: SearchResultCardProps) {
  const similarityPct = Math.round(result.similarity * 100);

  return (
    <Link href={`/admin/trends/${result.id}`}>
      <Card className="h-full hover:bg-muted/30 transition-colors cursor-pointer">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between gap-2">
            <CardTitle className="text-lg leading-tight">
              {result.title}
            </CardTitle>
            <span className="text-sm font-medium text-primary whitespace-nowrap">
              {similarityPct}% match
            </span>
          </div>
          <div className="flex flex-wrap gap-2 pt-1">
            <Badge
              variant="outline"
              className={
                result.trend_type === "rising"
                  ? "bg-orange-100 text-orange-800 border-orange-200"
                  : "bg-blue-100 text-blue-800 border-blue-200"
              }
            >
              {result.trend_type}
            </Badge>
            <Badge
              variant="outline"
              className={
                sentimentColors[result.sentiment] || sentimentColors.neutral
              }
            >
              {result.sentiment}
            </Badge>
            <Badge variant="secondary">{result.category}</Badge>
          </div>
        </CardHeader>
        <CardContent>
          <CardDescription className="text-sm leading-relaxed">
            {result.summary}
          </CardDescription>
          <p className="text-xs text-muted-foreground mt-3">
            {new Date(result.collected_at).toLocaleDateString()}
          </p>
        </CardContent>
      </Card>
    </Link>
  );
}

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
import type { TrendSearchResult } from "@/lib/types";

interface SearchResultCardProps {
  result: TrendSearchResult;
}

export function SearchResultCard({ result }: SearchResultCardProps) {
  const similarityPct = Math.round(result.similarity * 100);

  return (
    <Link href={`/trends/${result.id}`}>
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
                SENTIMENT_COLORS[result.sentiment] || SENTIMENT_COLORS.neutral
              }
            >
              {result.sentiment}
            </Badge>
            <Badge variant="secondary">{result.category}</Badge>
            {COLLECTION_TYPE_STYLES[result.collection_type] && (
              <Badge
                variant="outline"
                className={COLLECTION_TYPE_STYLES[result.collection_type].className}
              >
                {COLLECTION_TYPE_STYLES[result.collection_type].label}
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <CardDescription className="text-sm leading-relaxed">
            {result.summary}
          </CardDescription>
          <p className="text-xs text-muted-foreground mt-3">
            {new Date(result.collected_at).toLocaleString()}
          </p>
        </CardContent>
      </Card>
    </Link>
  );
}

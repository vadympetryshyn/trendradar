"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { getTrend } from "@/lib/api";
import { MarkdownContent } from "@/components/markdown-content";
import type { TrendDetail } from "@/lib/types";
import { stripSubredditPrefix } from "@/lib/format";

export default function TrendDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [trend, setTrend] = useState<TrendDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const id = params.id as string;

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    getTrend(id)
      .then(setTrend)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="py-8 text-center text-muted-foreground">Loading...</div>
    );
  }

  if (error || !trend) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8 space-y-4">
        <Button variant="outline" size="sm" onClick={() => router.back()}>
          &larr; Back
        </Button>
        <p className="text-red-500">{error || "Trend not found"}</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" size="sm" onClick={() => router.back()}>
          &larr; Back
        </Button>
        <div className="flex-1 min-w-0">
          <h1 className="text-2xl font-bold tracking-tight">{trend.title}</h1>
          <div className="flex flex-wrap gap-2 mt-2">
            <Badge
              variant="outline"
              className={
                trend.status === "active"
                  ? "bg-green-100 text-green-800 border-green-200"
                  : "bg-gray-100 text-gray-800 border-gray-200"
              }
            >
              {trend.status}
            </Badge>
            <Badge
              variant="outline"
              className={
                trend.sentiment === "positive"
                  ? "bg-green-100 text-green-800"
                  : trend.sentiment === "negative"
                    ? "bg-red-100 text-red-800"
                    : "bg-gray-100 text-gray-800"
              }
            >
              {trend.sentiment}
            </Badge>
            <Badge variant="secondary">{trend.category}</Badge>
            <Badge variant="outline" className={
              trend.collection_type === "rising"
                ? "bg-orange-100 text-orange-800 border-orange-200"
                : "bg-sky-100 text-sky-800 border-sky-200"
            }>
              {trend.collection_type === "now" ? "Now" : trend.collection_type === "rising" ? "Rising" : trend.collection_type === "daily" ? "Daily" : "Weekly"}
            </Badge>
            <Badge
              variant="outline"
              className="bg-blue-100 text-blue-800 border-blue-200"
            >
              {trend.mention_count} {trend.mention_count === 1 ? "mention" : "mentions"}
            </Badge>
            {trend.research_done && (
              <Badge
                variant="outline"
                className="bg-purple-100 text-purple-800 border-purple-200"
              >
                Researched
              </Badge>
            )}
          </div>
        </div>
      </div>

      {/* Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Summary</CardTitle>
          <CardDescription>
            Relevance: {Math.round(trend.relevance_score * 100)}% &middot;{" "}
            {trend.mention_count} mentions &middot; Collected{" "}
            {new Date(trend.collected_at).toLocaleString()}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm leading-relaxed">{trend.summary}</p>
        </CardContent>
      </Card>

      {/* Key Points */}
      {trend.key_points.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Key Points</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {trend.key_points.map((point, i) => (
                <li key={i} className="flex gap-2 text-sm">
                  <span className="text-primary mt-0.5 shrink-0">&#8226;</span>
                  <span>{point}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Research Context (read-only) */}
      {trend.research_done && trend.context_summary && (
        <Card>
          <CardHeader>
            <CardTitle>Research Context</CardTitle>
            <CardDescription>
              Researched at {new Date(trend.researched_at!).toLocaleString()}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="max-w-none">
              <MarkdownContent
                content={trend.context_summary}
                citations={trend.research_citations}
              />
            </div>
          </CardContent>
        </Card>
      )}

      {/* Sources */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {trend.source_subreddits.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Source Subreddits</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {trend.source_subreddits.map((sub) => {
                  const name = stripSubredditPrefix(sub);
                  return (
                    <a
                      key={sub}
                      href={`https://www.reddit.com/r/${name}/`}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <Badge variant="outline" className="cursor-pointer hover:bg-muted">
                        r/{name}
                      </Badge>
                    </a>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        )}

        {trend.source_urls.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Source URLs</CardTitle>
            </CardHeader>
            <CardContent className="space-y-1">
              {trend.source_urls.map((url, i) => (
                <a
                  key={i}
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block text-xs text-blue-500 hover:underline truncate"
                >
                  {url}
                </a>
              ))}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { JsonView, darkStyles } from "react-json-view-lite";
import "react-json-view-lite/dist/index.css";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { getAnalysisById } from "@/lib/api";
import type { TrendAnalysis } from "@/lib/types";
import { StatusBadge } from "../../_components/status-badge";

export default function TrendDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [analysis, setAnalysis] = useState<TrendAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedItems, setExpandedItems] = useState<Set<number>>(new Set());

  const id = Number(params.id);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    getAnalysisById(id)
      .then(setAnalysis)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  const toggleItem = (itemId: number) => {
    setExpandedItems((prev) => {
      const next = new Set(prev);
      if (next.has(itemId)) next.delete(itemId);
      else next.add(itemId);
      return next;
    });
  };

  const expandAll = () => {
    if (!analysis) return;
    setExpandedItems(new Set(analysis.trend_items.map((t) => t.id)));
  };

  const collapseAll = () => setExpandedItems(new Set());

  if (loading) {
    return (
      <div className="py-8 text-center text-muted-foreground">Loading...</div>
    );
  }

  if (error || !analysis) {
    return (
      <div className="space-y-4">
        <Button variant="outline" size="sm" onClick={() => router.back()}>
          &larr; Back
        </Button>
        <p className="text-red-500">{error || "Analysis not found"}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" size="sm" onClick={() => router.back()}>
          &larr; Back
        </Button>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            Analysis #{analysis.id}
          </h1>
          <p className="text-muted-foreground mt-1">
            Niche ID {analysis.niche_id}
          </p>
        </div>
      </div>

      {/* Overview card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Overview</CardTitle>
            <StatusBadge status={analysis.status} />
          </div>
          <CardDescription>
            {analysis.posts_fetched} posts fetched &middot;{" "}
            {analysis.subreddits_fetched} subreddits &middot;{" "}
            {analysis.trend_items.length} trend items
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <span className="text-muted-foreground">Started</span>
              <p>
                {analysis.started_at
                  ? new Date(analysis.started_at).toLocaleString()
                  : "—"}
              </p>
            </div>
            <div>
              <span className="text-muted-foreground">Completed</span>
              <p>
                {analysis.completed_at
                  ? new Date(analysis.completed_at).toLocaleString()
                  : "—"}
              </p>
            </div>
          </div>
          {analysis.overall_summary && (
            <div>
              <span className="text-muted-foreground">Summary</span>
              <p className="mt-1">{analysis.overall_summary}</p>
            </div>
          )}
          {analysis.error_message && (
            <div>
              <span className="text-muted-foreground">Error</span>
              <p className="mt-1 text-red-500">{analysis.error_message}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Trend Items */}
      {analysis.trend_items.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>
                Trend Items ({analysis.trend_items.length})
              </CardTitle>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={expandAll}>
                  Expand All
                </Button>
                <Button variant="outline" size="sm" onClick={collapseAll}>
                  Collapse All
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-2">
            {analysis.trend_items.map((item) => {
              const isOpen = expandedItems.has(item.id);
              return (
                <div key={item.id} className="rounded-lg border">
                  <button
                    className="flex w-full items-center justify-between px-4 py-3 text-left hover:bg-muted/50 transition-colors"
                    onClick={() => toggleItem(item.id)}
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <span className="text-muted-foreground text-xs shrink-0">
                        {isOpen ? "▼" : "▶"}
                      </span>
                      <span className="font-medium truncate">
                        {item.title}
                      </span>
                      <span
                        className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${
                          item.sentiment === "positive"
                            ? "bg-green-100 text-green-700"
                            : item.sentiment === "negative"
                              ? "bg-red-100 text-red-700"
                              : "bg-gray-100 text-gray-700"
                        }`}
                      >
                        {item.sentiment}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-muted-foreground shrink-0 ml-4">
                      <span>{item.category}</span>
                      <span>score: {item.relevance_score}</span>
                      <span>{item.mention_count} mentions</span>
                    </div>
                  </button>
                  {isOpen && (
                    <div className="border-t px-4 py-3 space-y-3">
                      <p className="text-sm">{item.summary}</p>

                      {item.key_points.length > 0 && (
                        <div>
                          <p className="text-xs font-medium text-muted-foreground mb-1">
                            Key Points
                          </p>
                          <ul className="list-disc list-inside text-sm space-y-0.5">
                            {item.key_points.map((point, i) => (
                              <li key={i}>{point}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {item.source_subreddits.length > 0 && (
                        <div>
                          <p className="text-xs font-medium text-muted-foreground mb-1">
                            Source Subreddits
                          </p>
                          <div className="flex flex-wrap gap-1">
                            {item.source_subreddits.map((sub) => (
                              <span
                                key={sub}
                                className="rounded bg-muted px-2 py-0.5 text-xs"
                              >
                                r/{sub}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {item.source_urls.length > 0 && (
                        <div>
                          <p className="text-xs font-medium text-muted-foreground mb-1">
                            Source URLs
                          </p>
                          <div className="space-y-0.5">
                            {item.source_urls.map((url, i) => (
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
                          </div>
                        </div>
                      )}

                      <details className="mt-2">
                        <summary className="cursor-pointer text-xs font-medium text-muted-foreground hover:text-foreground transition-colors">
                          Raw JSON
                        </summary>
                        <div className="mt-2 rounded-md bg-[#1e1e1e] p-3 overflow-auto max-h-[400px]">
                          <JsonView
                            data={item}
                            style={darkStyles}
                            shouldExpandNode={(level) => level < 1}
                          />
                        </div>
                      </details>
                    </div>
                  )}
                </div>
              );
            })}
          </CardContent>
        </Card>
      )}

      {/* Full Raw JSON */}
      <Card>
        <CardHeader>
          <CardTitle>Full Analysis JSON</CardTitle>
          <CardDescription>
            Complete raw data for this analysis
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-md bg-[#1e1e1e] p-4 overflow-auto max-h-[600px]">
            <JsonView
              data={analysis}
              style={darkStyles}
              shouldExpandNode={(level) => level < 2}
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

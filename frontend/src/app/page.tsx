"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { NicheSelector } from "@/components/niche-selector";
import { TrendsGrid } from "@/components/trends-grid";
import { getNiches, getLatestTrends } from "@/lib/api";
import type { Niche, TrendAnalysis } from "@/lib/types";

export default function Home() {
  const [niches, setNiches] = useState<Niche[]>([]);
  const [selectedNiche, setSelectedNiche] = useState("");
  const [analysis, setAnalysis] = useState<TrendAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getNiches()
      .then((data) => {
        setNiches(data);
        if (data.length > 0) {
          setSelectedNiche(data[0].slug);
        }
      })
      .catch((err) => setError(err.message));
  }, []);

  const handleShowTrends = async () => {
    if (!selectedNiche) return;
    setLoading(true);
    setError(null);
    setAnalysis(null);
    try {
      const data = await getLatestTrends(selectedNiche);
      setAnalysis(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch trends");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Trend Analysis</h1>
        <p className="text-muted-foreground mt-1">
          Discover what&apos;s trending across Reddit communities
        </p>
      </div>

      <div className="flex items-center gap-3">
        <NicheSelector
          niches={niches}
          selected={selectedNiche}
          onSelect={setSelectedNiche}
        />
        <Button onClick={handleShowTrends} disabled={!selectedNiche || loading}>
          {loading ? "Loading..." : "Show Trends"}
        </Button>
      </div>

      {error && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
          {error}
        </div>
      )}

      {loading && (
        <div className="space-y-4">
          <Skeleton className="h-24 w-full" />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-48" />
            ))}
          </div>
        </div>
      )}

      {analysis && !loading && <TrendsGrid analysis={analysis} />}

      {!analysis && !loading && !error && (
        <div className="text-center py-16 text-muted-foreground">
          Select a niche and click &quot;Show Trends&quot; to see the latest
          analysis
        </div>
      )}
    </div>
  );
}

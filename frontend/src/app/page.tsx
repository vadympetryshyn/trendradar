"use client";

import { useEffect, useRef, useState } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { TrendsGrid } from "@/components/trends-grid";
import { SearchResultCard } from "@/components/search-result-card";
import { getTrends, getNiches, searchTrends } from "@/lib/api";
import type { Niche, Trend, TrendSearchResult } from "@/lib/types";

export default function Home() {
  const [niches, setNiches] = useState<Niche[]>([]);
  const [trends, setTrends] = useState<Trend[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [trendTypeFilter, setTrendTypeFilter] = useState<string>("all");
  const [selectedNicheId, setSelectedNicheId] = useState<number | undefined>();

  // Search state
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<TrendSearchResult[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const isSearching = searchQuery.trim().length >= 2;

  useEffect(() => {
    getNiches()
      .then((data) => {
        setNiches(data);
        if (data.length > 0) {
          setSelectedNicheId(data[0].id);
        }
      })
      .catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    if (isSearching) return;
    if (!selectedNicheId) return;
    setLoading(true);
    setError(null);

    getTrends({
      niche_id: selectedNicheId,
      trend_type: trendTypeFilter === "all" ? undefined : trendTypeFilter,
      limit: 50,
    })
      .then((data) => setTrends(data.items))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [selectedNicheId, trendTypeFilter, isSearching]);

  // Debounced vector search
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);

    if (!isSearching) {
      setSearchResults([]);
      return;
    }

    debounceRef.current = setTimeout(() => {
      setSearchLoading(true);
      setError(null);

      searchTrends(searchQuery.trim(), undefined, 20)
        .then((data) => setSearchResults(data.results))
        .catch((err) => setError(err.message))
        .finally(() => setSearchLoading(false));
    }, 400);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [searchQuery, isSearching]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Trend Analysis</h1>
        <p className="text-muted-foreground mt-1">
          Discover what&apos;s trending across Reddit communities
        </p>
      </div>

      {/* Search input */}
      <div className="relative">
        <svg
          className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={2}
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z"
          />
        </svg>
        <input
          type="text"
          placeholder="Search trends by meaning, not just keywords..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full rounded-lg border border-input bg-background px-10 py-2.5 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
        />
        {searchQuery && (
          <button
            onClick={() => setSearchQuery("")}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
          >
            <svg
              className="h-4 w-4"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M6 18 18 6M6 6l12 12"
              />
            </svg>
          </button>
        )}
      </div>

      {/* Filters (hidden during search) */}
      {!isSearching && (
        <div className="flex items-center gap-3 flex-wrap">
          {niches.map((niche) => (
            <Badge
              key={niche.id}
              variant={selectedNicheId === niche.id ? "default" : "outline"}
              className="cursor-pointer text-sm px-3 py-1"
              onClick={() => setSelectedNicheId(niche.id)}
            >
              {niche.name}
            </Badge>
          ))}

          <div className="h-6 w-px bg-border mx-1" />

          {["all", "hot", "rising"].map((type) => (
            <Badge
              key={type}
              variant={trendTypeFilter === type ? "default" : "outline"}
              className="cursor-pointer text-sm px-3 py-1"
              onClick={() => setTrendTypeFilter(type)}
            >
              {type === "all" ? "All" : type === "hot" ? "Hot" : "Rising"}
            </Badge>
          ))}
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
          {error}
        </div>
      )}

      {/* Search results */}
      {isSearching && (
        <>
          {searchLoading && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-48" />
              ))}
            </div>
          )}
          {!searchLoading && searchResults.length === 0 && (
            <div className="text-center py-16 text-muted-foreground">
              No matching trends found.
            </div>
          )}
          {!searchLoading && searchResults.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {searchResults.map((result) => (
                <SearchResultCard key={result.id} result={result} />
              ))}
            </div>
          )}
        </>
      )}

      {/* Browse mode */}
      {!isSearching && (
        <>
          {loading && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-48" />
              ))}
            </div>
          )}
          {!loading && <TrendsGrid trends={trends} />}
        </>
      )}
    </div>
  );
}

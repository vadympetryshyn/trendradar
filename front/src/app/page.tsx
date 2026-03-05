"use client";

import { useEffect, useState } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { TrendsGrid } from "@/components/trends-grid";
import { SearchResultCard } from "@/components/search-result-card";
import { getTrends, getNiches, searchTrends } from "@/lib/api";
import type { Niche, Trend, TrendSearchResult } from "@/lib/types";

const COLLECTION_TABS = [
  { value: "now" as const, label: "Trending Now" },
  { value: "rising" as const, label: "Rising" },
  { value: "daily" as const, label: "Today's Trends" },
  { value: "weekly" as const, label: "This Week" },
];

export default function Home() {
  const [niches, setNiches] = useState<Niche[]>([]);
  const [trends, setTrends] = useState<Trend[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedNicheId, setSelectedNicheId] = useState<number | undefined>();

  // Collection type filter
  const [collectionType, setCollectionType] = useState<"now" | "daily" | "weekly" | "rising">("now");

  // Tab counts
  const [tabCounts, setTabCounts] = useState<Record<string, number>>({});

  // Search state
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<TrendSearchResult[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const isSearching = hasSearched;

  useEffect(() => {
    getNiches()
      .then((data) => {
        setNiches(data);
      })
      .catch((err) => setError(err.message));
  }, []);

  // Fetch counts for all tabs when niche changes
  useEffect(() => {
    Promise.all(
      COLLECTION_TABS.map((tab) =>
        getTrends({ niche_id: selectedNicheId, collection_type: tab.value, limit: 1 })
          .then((data) => [tab.value, data.total] as const)
      )
    )
      .then((entries) => setTabCounts(Object.fromEntries(entries)))
      .catch(() => {});
  }, [selectedNicheId]);

  useEffect(() => {
    if (isSearching) return;
    setLoading(true);
    setError(null);

    getTrends({
      niche_id: selectedNicheId,
      collection_type: collectionType,
      limit: 50,
    })
      .then((data) => {
        setTrends(data.items);
        setTabCounts((prev) => ({ ...prev, [collectionType]: data.total }));
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [selectedNicheId, isSearching, collectionType]);

  const handleSearch = () => {
    if (searchQuery.trim().length < 2) return;
    setHasSearched(true);
    setSearchLoading(true);
    setError(null);

    searchTrends(searchQuery.trim(), undefined, 20)
      .then((data) => setSearchResults(data.results))
      .catch((err) => setError(err.message))
      .finally(() => setSearchLoading(false));
  };

  const handleClear = () => {
    setSearchQuery("");
    setSearchResults([]);
    setHasSearched(false);
  };

  const handleCollectionTypeChange = (ct: "now" | "daily" | "weekly" | "rising") => {
    setCollectionType(ct);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Trend Analysis</h1>
        <p className="text-muted-foreground mt-1">
          Discover what&apos;s trending across Reddit communities
        </p>
      </div>

      {/* Search input */}
      <div className="flex gap-2">
        <div className="relative flex-1">
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
            onChange={(e) => {
            setSearchQuery(e.target.value);
            if (e.target.value.trim() === "") {
              setHasSearched(false);
              setSearchResults([]);
            }
          }}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            className="w-full rounded-lg border border-input bg-background px-10 py-2.5 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          />
          {searchQuery && (
            <button
              onClick={handleClear}
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
        <button
          onClick={handleSearch}
          disabled={searchQuery.trim().length < 2 || searchLoading}
          className="rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:pointer-events-none"
        >
          Search
        </button>
      </div>

      {/* Niche filter + Collection type tabs (hidden during search) */}
      {!isSearching && (
        <div className="flex flex-wrap items-center gap-2">
          {niches.length > 0 && (
            <select
              value={selectedNicheId ?? ""}
              onChange={(e) => {
                const val = e.target.value;
                setSelectedNicheId(val === "" ? undefined : Number(val));
              }}
              className="cursor-pointer rounded-lg border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            >
              <option value="">All Niches</option>
              {niches.map((niche) => (
                <option key={niche.id} value={niche.id}>
                  {niche.name}
                </option>
              ))}
            </select>
          )}
          {COLLECTION_TABS.map((tab) => (
            <button
              key={tab.value}
              onClick={() => handleCollectionTypeChange(tab.value)}
              className={`cursor-pointer rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                collectionType === tab.value
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground hover:text-foreground"
              }`}
            >
              {tab.label}
              {tabCounts[tab.value] !== undefined && (
                <span className="ml-1.5 text-xs opacity-70">({tabCounts[tab.value]})</span>
              )}
            </button>
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

"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Trash2 } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Checkbox } from "@/components/ui/checkbox";
import { getTrends, getNiches, deleteTrendsBulk } from "@/lib/api";
import type { Niche, Trend } from "@/lib/types";

export default function TrendsPage() {
  const router = useRouter();
  const [niches, setNiches] = useState<Niche[]>([]);
  const [trends, setTrends] = useState<Trend[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [offset, setOffset] = useState(0);
  const [nicheFilter, setNicheFilter] = useState<number | undefined>();
  const [typeFilter, setTypeFilter] = useState<string | undefined>();
  const [statusFilter, setStatusFilter] = useState<string>("active");
  const [researchedFilter, setResearchedFilter] = useState<string>("all");
  const [embeddingFilter, setEmbeddingFilter] = useState<string>("all");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [deleting, setDeleting] = useState(false);
  const limit = 20;

  useEffect(() => {
    getNiches().then(setNiches);
  }, []);

  useEffect(() => {
    setLoading(true);
    getTrends({
      niche_id: nicheFilter,
      trend_type: typeFilter,
      limit,
      offset,
    })
      .then((data) => {
        let items = data.items;
        if (statusFilter !== "all") {
          items = items.filter((t) => t.status === statusFilter);
        }
        if (researchedFilter === "yes") {
          items = items.filter((t) => t.research_done);
        } else if (researchedFilter === "no") {
          items = items.filter((t) => !t.research_done);
        }
        if (embeddingFilter === "yes") {
          items = items.filter((t) => t.has_embedding);
        } else if (embeddingFilter === "no") {
          items = items.filter((t) => !t.has_embedding);
        }
        setTrends(items);
        setTotal(data.total);
      })
      .finally(() => setLoading(false));
  }, [nicheFilter, typeFilter, offset, statusFilter, researchedFilter, embeddingFilter]);

  const totalPages = Math.ceil(total / limit);
  const currentPage = Math.floor(offset / limit) + 1;

  const allSelected = trends.length > 0 && trends.every((t) => selectedIds.has(t.id));

  const toggleSelectAll = () => {
    if (allSelected) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(trends.map((t) => t.id)));
    }
  };

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const handleBulkDelete = async () => {
    if (selectedIds.size === 0) return;
    setDeleting(true);
    try {
      await deleteTrendsBulk(Array.from(selectedIds));
      setTrends((prev) => prev.filter((t) => !selectedIds.has(t.id)));
      setTotal((prev) => prev - selectedIds.size);
      setSelectedIds(new Set());
    } catch {
      alert("Failed to delete trends");
    } finally {
      setDeleting(false);
    }
  };

  if (loading && trends.length === 0) {
    return (
      <div className="py-8 text-center text-muted-foreground">Loading...</div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Trends Browser</h1>
          <p className="text-muted-foreground mt-1">
            Browse and filter all collected trends
          </p>
        </div>
        {selectedIds.size > 0 && (
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="destructive" disabled={deleting}>
                <Trash2 className="h-4 w-4 mr-2" />
                {deleting ? "Deleting..." : `Delete Selected (${selectedIds.size})`}
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Delete {selectedIds.size} trend(s)</AlertDialogTitle>
                <AlertDialogDescription>
                  Permanently delete the selected trends? This action cannot be undone.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction onClick={handleBulkDelete}>
                  Delete
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2 items-center">
        <Badge
          variant={!nicheFilter ? "default" : "outline"}
          className="cursor-pointer"
          onClick={() => { setNicheFilter(undefined); setOffset(0); }}
        >
          All Niches
        </Badge>
        {niches.map((n) => (
          <Badge
            key={n.id}
            variant={nicheFilter === n.id ? "default" : "outline"}
            className="cursor-pointer"
            onClick={() => { setNicheFilter(n.id); setOffset(0); }}
          >
            {n.name}
          </Badge>
        ))}

        <div className="h-6 w-px bg-border mx-1" />

        {["all", "hot", "rising"].map((type) => (
          <Badge
            key={type}
            variant={
              (type === "all" && !typeFilter) || typeFilter === type
                ? "default"
                : "outline"
            }
            className="cursor-pointer"
            onClick={() => {
              setTypeFilter(type === "all" ? undefined : type);
              setOffset(0);
            }}
          >
            {type === "all" ? "All Types" : type}
          </Badge>
        ))}

        <div className="h-6 w-px bg-border mx-1" />

        {["all", "active", "expired"].map((s) => (
          <Badge
            key={s}
            variant={statusFilter === s ? "default" : "outline"}
            className="cursor-pointer"
            onClick={() => { setStatusFilter(s); setOffset(0); }}
          >
            {s === "all" ? "All Status" : s}
          </Badge>
        ))}

        <div className="h-6 w-px bg-border mx-1" />

        {["all", "yes", "no"].map((r) => (
          <Badge
            key={r}
            variant={embeddingFilter === r ? "default" : "outline"}
            className="cursor-pointer"
            onClick={() => { setEmbeddingFilter(r); setOffset(0); }}
          >
            {r === "all"
              ? "All Embeds"
              : r === "yes"
                ? "Embedded"
                : "No Embed"}
          </Badge>
        ))}

        <div className="h-6 w-px bg-border mx-1" />

        {["all", "yes", "no"].map((r) => (
          <Badge
            key={r}
            variant={researchedFilter === r ? "default" : "outline"}
            className="cursor-pointer"
            onClick={() => { setResearchedFilter(r); setOffset(0); }}
          >
            {r === "all"
              ? "All Research"
              : r === "yes"
                ? "Researched"
                : "Not Researched"}
          </Badge>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Trends</CardTitle>
          <CardDescription>{total} total</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-muted-foreground">
                  <th className="pb-2 pr-4 font-medium w-10">
                    <Checkbox
                      checked={allSelected}
                      onCheckedChange={toggleSelectAll}
                    />
                  </th>
                  <th className="pb-2 pr-4 font-medium">Title</th>
                  <th className="pb-2 pr-4 font-medium">Type</th>
                  <th className="pb-2 pr-4 font-medium">Sentiment</th>
                  <th className="pb-2 pr-4 font-medium">Category</th>
                  <th className="pb-2 pr-4 font-medium text-right">Score</th>
                  <th className="pb-2 pr-4 font-medium text-right">Mentions</th>
                  <th className="pb-2 pr-4 font-medium">Embed</th>
                  <th className="pb-2 pr-4 font-medium">Researched</th>
                  <th className="pb-2 font-medium">Collected</th>
                </tr>
              </thead>
              <tbody>
                {trends.map((trend) => (
                  <tr
                    key={trend.id}
                    className={`border-b last:border-0 cursor-pointer hover:bg-muted/50 transition-colors ${selectedIds.has(trend.id) ? "bg-muted/30" : ""}`}
                    onClick={() => router.push(`/admin/trends/${trend.id}`)}
                  >
                    <td className="py-3 pr-4" onClick={(e) => e.stopPropagation()}>
                      <Checkbox
                        checked={selectedIds.has(trend.id)}
                        onCheckedChange={() => toggleSelect(trend.id)}
                      />
                    </td>
                    <td className="py-3 pr-4 font-medium max-w-[300px] truncate">
                      {trend.title}
                    </td>
                    <td className="py-3 pr-4">
                      <Badge
                        variant="outline"
                        className={
                          trend.trend_type === "rising"
                            ? "bg-orange-100 text-orange-800"
                            : "bg-blue-100 text-blue-800"
                        }
                      >
                        {trend.trend_type}
                      </Badge>
                    </td>
                    <td className="py-3 pr-4">
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
                    </td>
                    <td className="py-3 pr-4 text-muted-foreground">
                      {trend.category}
                    </td>
                    <td className="py-3 pr-4 text-right tabular-nums">
                      {Math.round(trend.relevance_score * 100)}%
                    </td>
                    <td className="py-3 pr-4 text-right tabular-nums">
                      {trend.mention_count}
                    </td>
                    <td className="py-3 pr-4">
                      {trend.has_embedding ? (
                        <Badge variant="outline" className="bg-purple-100 text-purple-800">
                          Yes
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="text-muted-foreground">
                          No
                        </Badge>
                      )}
                    </td>
                    <td className="py-3 pr-4">
                      {trend.research_done ? (
                        <Badge variant="outline" className="bg-green-100 text-green-800">
                          Yes
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="text-muted-foreground">
                          No
                        </Badge>
                      )}
                    </td>
                    <td className="py-3 text-muted-foreground">
                      {new Date(trend.collected_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
                {trends.length === 0 && (
                  <tr>
                    <td
                      colSpan={10}
                      className="py-8 text-center text-muted-foreground"
                    >
                      No trends found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-between pt-4">
              <p className="text-sm text-muted-foreground">
                Page {currentPage} of {totalPages}
              </p>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  disabled={offset <= 0}
                  onClick={() => setOffset((o) => Math.max(0, o - limit))}
                >
                  Previous
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  disabled={currentPage >= totalPages}
                  onClick={() => setOffset((o) => o + limit)}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

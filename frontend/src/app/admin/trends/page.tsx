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
import { getAnalyses, deleteAnalysis } from "@/lib/api";
import type { AnalysisListItem } from "@/lib/types";
import { StatusBadge } from "../_components/status-badge";

export default function TrendsPage() {
  const router = useRouter();
  const [items, setItems] = useState<AnalysisListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const perPage = 20;

  useEffect(() => {
    setLoading(true);
    getAnalyses(page, perPage)
      .then((data) => {
        setItems(data.items);
        setTotal(data.total);
      })
      .finally(() => setLoading(false));
  }, [page]);

  const handleDelete = async (id: number) => {
    setDeletingId(id);
    try {
      await deleteAnalysis(id);
      setItems((prev) => prev.filter((item) => item.id !== id));
      setTotal((prev) => prev - 1);
    } catch {
      alert("Failed to delete analysis");
    } finally {
      setDeletingId(null);
    }
  };

  const totalPages = Math.ceil(total / perPage);

  if (loading && items.length === 0) {
    return (
      <div className="py-8 text-center text-muted-foreground">Loading...</div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Trends</h1>
        <p className="text-muted-foreground mt-1">
          All trend analyses across niches
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Analyses</CardTitle>
          <CardDescription>
            {total} total analys{total === 1 ? "is" : "es"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-muted-foreground">
                  <th className="pb-2 pr-4 font-medium w-10">#</th>
                  <th className="pb-2 pr-4 font-medium">Niche</th>
                  <th className="pb-2 pr-4 font-medium">Status</th>
                  <th className="pb-2 pr-4 font-medium text-right">Posts</th>
                  <th className="pb-2 pr-4 font-medium text-right">Trends</th>
                  <th className="pb-2 pr-4 font-medium">Started</th>
                  <th className="pb-2 pr-4 font-medium">Completed</th>
                  <th className="pb-2 font-medium w-10" />
                </tr>
              </thead>
              <tbody>
                {items.map((item, index) => (
                  <tr
                    key={item.id}
                    className="border-b last:border-0 cursor-pointer hover:bg-muted/50 transition-colors"
                    onClick={() => router.push(`/admin/trends/${item.id}`)}
                  >
                    <td className="py-3 pr-4 text-muted-foreground tabular-nums">
                      {(page - 1) * perPage + index + 1}
                    </td>
                    <td className="py-3 pr-4 font-medium">{item.niche_name}</td>
                    <td className="py-3 pr-4">
                      <StatusBadge status={item.status} />
                    </td>
                    <td className="py-3 pr-4 text-right tabular-nums">
                      {item.posts_fetched}
                    </td>
                    <td className="py-3 pr-4 text-right tabular-nums">
                      {item.trend_items_count}
                    </td>
                    <td className="py-3 pr-4 text-muted-foreground">
                      {item.started_at
                        ? new Date(item.started_at).toLocaleString()
                        : "—"}
                    </td>
                    <td className="py-3 pr-4 text-muted-foreground">
                      {item.completed_at
                        ? new Date(item.completed_at).toLocaleString()
                        : "—"}
                    </td>
                    <td className="py-3" onClick={(e) => e.stopPropagation()}>
                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <Button
                            size="icon-xs"
                            variant="ghost"
                            disabled={deletingId === item.id}
                            className="text-muted-foreground hover:text-destructive"
                          >
                            <Trash2 />
                          </Button>
                        </AlertDialogTrigger>
                        <AlertDialogContent>
                          <AlertDialogHeader>
                            <AlertDialogTitle>Delete analysis</AlertDialogTitle>
                            <AlertDialogDescription>
                              This will permanently delete this analysis and all
                              its trend items. This action cannot be undone.
                            </AlertDialogDescription>
                          </AlertDialogHeader>
                          <AlertDialogFooter>
                            <AlertDialogCancel>Cancel</AlertDialogCancel>
                            <AlertDialogAction
                              variant="destructive"
                              onClick={() => handleDelete(item.id)}
                            >
                              Delete
                            </AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                    </td>
                  </tr>
                ))}
                {items.length === 0 && (
                  <tr>
                    <td
                      colSpan={8}
                      className="py-8 text-center text-muted-foreground"
                    >
                      No analyses found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-between pt-4">
              <p className="text-sm text-muted-foreground">
                Page {page} of {totalPages}
              </p>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => p - 1)}
                >
                  Previous
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => p + 1)}
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

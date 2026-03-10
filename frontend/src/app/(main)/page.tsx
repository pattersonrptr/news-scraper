"use client";

import { useState } from "react";
import { useArticles } from "@/lib/hooks";
import { ArticleCard } from "@/components/article-card";
import { ArticleDrawer } from "@/components/article-drawer";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import type { Article } from "@/lib/schemas";

const SENTIMENTS = [
  { label: "All", value: "" },
  { label: "Positive", value: "1" },
  { label: "Neutral", value: "0" },
  { label: "Negative", value: "-1" },
];

/** Mirrors the ArticleCard layout while data is loading. */
function ArticleCardSkeleton() {
  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          {/* title — two lines */}
          <div className="flex-1 space-y-1.5">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
          </div>
          {/* sentiment icon */}
          <Skeleton className="h-4 w-4 shrink-0 rounded-full" />
        </div>
        {/* category badge */}
        <div className="pt-1">
          <Skeleton className="h-5 w-20 rounded-full" />
        </div>
      </CardHeader>
      <CardContent className="pt-0 space-y-2">
        {/* summary — two lines */}
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-5/6" />
        {/* date */}
        <Skeleton className="h-3 w-24 mt-1" />
      </CardContent>
    </Card>
  );
}

export default function FeedPage() {
  const PAGE_SIZE = 20;
  const [offset, setOffset] = useState(0);
  const [category, setCategory] = useState("");
  const [sentiment, setSentiment] = useState("");
  const [selectedArticle, setSelectedArticle] = useState<Article | null>(null);

  const { data, isLoading, isError } = useArticles({
    limit: PAGE_SIZE,
    offset,
    category: category || undefined,
    sentiment: sentiment !== "" ? Number(sentiment) : undefined,
  });

  const page = Math.floor(offset / PAGE_SIZE) + 1;
  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 1;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-bold">Feed</h1>
        <div className="ml-auto flex flex-wrap gap-2">
          <Input
            placeholder="Filter by category…"
            value={category}
            onChange={(e) => { setCategory(e.target.value); setOffset(0); }}
            className="w-40"
          />
          <select
            value={sentiment}
            onChange={(e) => { setSentiment(e.target.value); setOffset(0); }}
            className="h-10 rounded-md border border-input bg-background px-3 text-sm"
          >
            {SENTIMENTS.map((s) => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>
        </div>
      </div>

      {isError && <p className="text-destructive">Failed to load articles.</p>}

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {isLoading
          ? Array.from({ length: 8 }).map((_, i) => <ArticleCardSkeleton key={i} />)
          : data?.items.map((article) => (
              <ArticleCard
                key={article.id}
                article={article}
                onClick={() => setSelectedArticle(article)}
              />
            ))}
      </div>

      {data && totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={offset === 0}
            onClick={() => setOffset((o) => Math.max(0, o - PAGE_SIZE))}
          >
            Previous
          </Button>
          <span className="text-sm text-muted-foreground">
            Page {page} / {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= totalPages}
            onClick={() => setOffset((o) => o + PAGE_SIZE)}
          >
            Next
          </Button>
        </div>
      )}

      <ArticleDrawer
        article={selectedArticle}
        onClose={() => setSelectedArticle(null)}
      />
    </div>
  );
}

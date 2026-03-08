"use client";

import { useState } from "react";
import { useArticles } from "@/lib/hooks";
import { ArticleCard } from "@/components/article-card";
import { ArticleDrawer } from "@/components/article-drawer";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { Article } from "@/lib/schemas";

const SENTIMENTS = [
  { label: "All", value: "" },
  { label: "Positive", value: "1" },
  { label: "Neutral", value: "0" },
  { label: "Negative", value: "-1" },
];

export default function FeedPage() {
  const [page, setPage] = useState(1);
  const [category, setCategory] = useState("");
  const [sentiment, setSentiment] = useState("");
  const [selectedArticle, setSelectedArticle] = useState<Article | null>(null);

  const { data, isLoading, isError } = useArticles({
    page,
    page_size: 20,
    category: category || undefined,
    sentiment: sentiment !== "" ? Number(sentiment) : undefined,
  });

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-bold">Feed</h1>
        <div className="ml-auto flex flex-wrap gap-2">
          <Input
            placeholder="Filter by category…"
            value={category}
            onChange={(e) => { setCategory(e.target.value); setPage(1); }}
            className="w-40"
          />
          <select
            value={sentiment}
            onChange={(e) => { setSentiment(e.target.value); setPage(1); }}
            className="h-10 rounded-md border border-input bg-background px-3 text-sm"
          >
            {SENTIMENTS.map((s) => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>
        </div>
      </div>

      {isLoading && <p className="text-muted-foreground">Loading…</p>}
      {isError && <p className="text-destructive">Failed to load articles.</p>}

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {data?.items.map((article) => (
          <ArticleCard
            key={article.id}
            article={article}
            onClick={() => setSelectedArticle(article)}
          />
        ))}
      </div>

      {data && data.meta.pages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
          >
            Previous
          </Button>
          <span className="text-sm text-muted-foreground">
            Page {data.meta.page} / {data.meta.pages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= data.meta.pages}
            onClick={() => setPage((p) => p + 1)}
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

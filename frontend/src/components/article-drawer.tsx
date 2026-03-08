"use client";

import { ExternalLink } from "lucide-react";
import { Drawer } from "@/components/ui/drawer";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { sentimentLabel, sentimentColor, formatDate } from "@/lib/utils";
import { useMarkRead } from "@/lib/hooks";
import type { Article } from "@/lib/schemas";

interface ArticleDrawerProps {
  article: Article | null;
  onClose: () => void;
}

export function ArticleDrawer({ article, onClose }: ArticleDrawerProps) {
  const markRead = useMarkRead();

  if (!article) return null;

  return (
    <Drawer open={!!article} onClose={onClose} title={article.title}>
      <div className="space-y-4">
        {/* Meta row */}
        <div className="flex flex-wrap gap-2 text-sm text-muted-foreground">
          {article.category && (
            <Badge variant="secondary" className="capitalize">{article.category}</Badge>
          )}
          <span className={sentimentColor(article.sentiment)}>
            {sentimentLabel(article.sentiment)}
          </span>
          {article.relevance_score != null && (
            <span>Relevance: {(article.relevance_score * 100).toFixed(0)}%</span>
          )}
          <span>{formatDate(article.published_at ?? article.collected_at)}</span>
        </div>

        {/* Summary */}
        {article.summary && (
          <div>
            <h3 className="mb-1 font-semibold">Summary</h3>
            <p className="text-sm leading-relaxed text-muted-foreground">{article.summary}</p>
          </div>
        )}

        {/* Entities */}
        {article.entities && Object.keys(article.entities).length > 0 && (
          <div>
            <h3 className="mb-1 font-semibold">Entities</h3>
            <div className="flex flex-wrap gap-1">
              {Object.entries(article.entities).map(([type, values]) =>
                (values as string[]).map((v) => (
                  <Badge key={`${type}-${v}`} variant="outline" className="text-xs">
                    <span className="text-muted-foreground mr-1">{type}:</span>
                    {v}
                  </Badge>
                )),
              )}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-2 pt-2">
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center justify-center rounded-md border border-input bg-background px-3 py-2 text-sm font-medium hover:bg-accent hover:text-accent-foreground"
          >
            <ExternalLink className="mr-2 h-4 w-4" />
            Open original
          </a>
          {!article.is_read && (
            <Button
              size="sm"
              disabled={markRead.isPending}
              onClick={() => markRead.mutate(article.id)}
            >
              Mark as read
            </Button>
          )}
        </div>
      </div>
    </Drawer>
  );
}

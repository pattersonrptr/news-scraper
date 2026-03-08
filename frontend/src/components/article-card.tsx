"use client";

import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatDate } from "@/lib/utils";
import type { Article } from "@/lib/schemas";

interface ArticleCardProps {
  article: Article;
  onClick: () => void;
}

function SentimentIcon({ value }: { value: number }) {
  if (value > 0) return <TrendingUp className="h-4 w-4 text-green-500" />;
  if (value < 0) return <TrendingDown className="h-4 w-4 text-red-500" />;
  return <Minus className="h-4 w-4 text-yellow-500" />;
}

export function ArticleCard({ article, onClick }: ArticleCardProps) {
  return (
    <Card
      className="cursor-pointer transition-shadow hover:shadow-md"
      onClick={onClick}
    >
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="line-clamp-2 text-base leading-snug">
            {article.title}
          </CardTitle>
          <SentimentIcon value={article.sentiment} />
        </div>
        <div className="flex flex-wrap gap-1 pt-1">
          {article.category && (
            <Badge variant="secondary" className="capitalize">
              {article.category}
            </Badge>
          )}
          {article.is_read && (
            <Badge variant="outline" className="text-xs">
              Read
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        {article.summary && (
          <p className="line-clamp-2 text-sm text-muted-foreground">{article.summary}</p>
        )}
        <p className="mt-2 text-xs text-muted-foreground">
          {formatDate(article.published_at ?? article.collected_at)}
        </p>
      </CardContent>
    </Card>
  );
}

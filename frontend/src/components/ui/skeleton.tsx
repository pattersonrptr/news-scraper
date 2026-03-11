import { cn } from "@/lib/utils";

/**
 * Skeleton — animated shimmer placeholder.
 * Drop-in for any block of content while data is loading.
 * Usage: <Skeleton className="h-4 w-32" />
 */
export function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("animate-pulse rounded-md bg-muted", className)}
      {...props}
    />
  );
}

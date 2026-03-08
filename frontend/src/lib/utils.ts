import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Map sentiment int (-1, 0, 1) to a human-readable label. */
export function sentimentLabel(s: number): string {
  if (s > 0) return "Positive";
  if (s < 0) return "Negative";
  return "Neutral";
}

/** Map sentiment int to a Tailwind color class. */
export function sentimentColor(s: number): string {
  if (s > 0) return "text-green-600 dark:text-green-400";
  if (s < 0) return "text-red-500 dark:text-red-400";
  return "text-yellow-500 dark:text-yellow-400";
}

/** Format an ISO date string to a readable short form. */
export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(iso));
}

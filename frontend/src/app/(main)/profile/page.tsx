"use client";

import { useState } from "react";
import { useProfile, useUpdateProfile } from "@/lib/hooks";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { X, Plus, BookOpen, TrendingUp, Info } from "lucide-react";
import { toast } from "sonner";

// Colour palette cycled by index for category badges
const CATEGORY_COLOURS = [
  "bg-blue-100 text-blue-800",
  "bg-green-100 text-green-800",
  "bg-purple-100 text-purple-800",
  "bg-amber-100 text-amber-800",
  "bg-rose-100 text-rose-800",
  "bg-cyan-100 text-cyan-800",
  "bg-indigo-100 text-indigo-800",
  "bg-orange-100 text-orange-800",
];

export default function ProfilePage() {
  const { data: profile, isLoading } = useProfile();
  const updateProfile = useUpdateProfile();
  const [newInterest, setNewInterest] = useState("");

  const interests = profile?.explicit_interests ?? [];

  const addInterest = async () => {
    const kw = newInterest.trim().toLowerCase();
    if (!kw) return;
    if (interests.includes(kw)) {
      toast.error(`"${kw}" is already in your interests.`);
      return;
    }
    try {
      await updateProfile.mutateAsync([...interests, kw]);
      toast.success(`Added "${kw}" to interests.`);
      setNewInterest("");
    } catch {
      toast.error("Failed to update interests. Please try again.");
    }
  };

  const removeInterest = async (kw: string) => {
    try {
      await updateProfile.mutateAsync(interests.filter((i) => i !== kw));
      toast.success(`Removed "${kw}" from interests.`);
    } catch {
      toast.error("Failed to update interests. Please try again.");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      addInterest();
    }
  };

  // Sort by weight descending; compute max for relative bar widths
  const implicitEntries = Object.entries(profile?.implicit_weights ?? {}).sort(
    ([, a], [, b]) => b - a,
  );
  const maxWeight = implicitEntries.length > 0 ? implicitEntries[0][1] : 1;

  if (isLoading) return <p className="text-muted-foreground">Loading…</p>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Profile & Interests</h1>

      {/* ------------------------------------------------------------------ */}
      {/* Explicit interests                                                   */}
      {/* ------------------------------------------------------------------ */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <BookOpen className="h-5 w-5 text-muted-foreground" />
            <CardTitle>Explicit Interests</CardTitle>
          </div>
          <CardDescription>
            Keywords used to score article relevance. Add topics you care about.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {interests.map((kw) => (
              <Badge key={kw} variant="default" className="gap-1 pr-1">
                {kw}
                <button
                  onClick={() => removeInterest(kw)}
                  className="ml-1 rounded-full hover:bg-primary-foreground/20"
                  aria-label={`Remove ${kw}`}
                  disabled={updateProfile.isPending}
                >
                  <X className="h-3 w-3" />
                </button>
              </Badge>
            ))}
            {interests.length === 0 && (
              <p className="text-sm text-muted-foreground">
                No explicit interests yet. Add some keywords below.
              </p>
            )}
          </div>
          <div className="flex gap-2">
            <Input
              value={newInterest}
              onChange={(e) => setNewInterest(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="e.g. python, climate, AI…"
              className="max-w-xs"
              disabled={updateProfile.isPending}
            />
            <Button
              size="sm"
              onClick={addInterest}
              disabled={updateProfile.isPending || !newInterest.trim()}
            >
              <Plus className="mr-1 h-4 w-4" />
              Add
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* ------------------------------------------------------------------ */}
      {/* Implicit weights                                                     */}
      {/* ------------------------------------------------------------------ */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-muted-foreground" />
            <CardTitle>Reading Habits</CardTitle>
          </div>
          <CardDescription>
            Automatically inferred from the articles you mark as read. Updated
            in real time as you read; also recalculated daily with a small decay
            (×&nbsp;0.995) so older habits fade naturally.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {implicitEntries.length === 0 ? (
            <div className="flex items-start gap-3 rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
              <Info className="mt-0.5 h-4 w-4 shrink-0" />
              <p>
                No reading data yet. Open any article and mark it as read — its
                category will appear here and influence the relevance scores of
                future articles.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {implicitEntries.map(([category, weight], idx) => {
                const pct = maxWeight > 0 ? (weight / maxWeight) * 100 : 0;
                const colour = CATEGORY_COLOURS[idx % CATEGORY_COLOURS.length];
                return (
                  <div key={category} className="flex items-center gap-3">
                    <span
                      className={`inline-flex w-28 shrink-0 items-center justify-center rounded-full px-2 py-0.5 text-xs font-medium capitalize ${colour}`}
                    >
                      {category}
                    </span>
                    <div className="flex-1 overflow-hidden rounded-full bg-muted h-2">
                      <div
                        className="h-2 rounded-full bg-primary transition-all duration-500"
                        style={{ width: `${pct.toFixed(1)}%` }}
                      />
                    </div>
                    <span className="w-10 shrink-0 text-right text-xs tabular-nums text-muted-foreground">
                      {weight.toFixed(2)}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}


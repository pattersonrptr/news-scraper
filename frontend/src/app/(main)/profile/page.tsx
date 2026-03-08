"use client";

import { useState } from "react";
import { useProfile, useUpdateProfile } from "@/lib/hooks";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { X, Plus } from "lucide-react";

export default function ProfilePage() {
  const { data: profile, isLoading } = useProfile();
  const updateProfile = useUpdateProfile();
  const [newKeyword, setNewKeyword] = useState("");

  const interests = profile?.explicit_interests ?? [];

  const addKeyword = () => {
    const kw = newKeyword.trim().toLowerCase();
    if (!kw || interests.includes(kw)) return;
    updateProfile.mutate([...interests, kw]);
    setNewKeyword("");
  };

  const removeKeyword = (kw: string) => {
    updateProfile.mutate(interests.filter((i) => i !== kw));
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      addKeyword();
    }
  };

  const implicitWeights = Object.entries(profile?.implicit_weights ?? {}).sort(
    ([, a], [, b]) => b - a,
  );

  if (isLoading) return <p className="text-muted-foreground">Loading…</p>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Profile</h1>

      {/* Interests */}
      <Card>
        <CardHeader>
          <CardTitle>Interests</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {interests.map((kw) => (
              <Badge key={kw} variant="default" className="gap-1 pr-1">
                {kw}
                <button
                  onClick={() => removeKeyword(kw)}
                  className="ml-1 rounded-full hover:bg-primary-foreground/20"
                  aria-label={`Remove ${kw}`}
                >
                  <X className="h-3 w-3" />
                </button>
              </Badge>
            ))}
            {interests.length === 0 && (
              <p className="text-sm text-muted-foreground">No interests yet.</p>
            )}
          </div>
          <div className="flex gap-2">
            <Input
              value={newKeyword}
              onChange={(e) => setNewKeyword(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Add keyword (e.g. python, climate…)"
              className="max-w-xs"
            />
            <Button size="sm" onClick={addKeyword} disabled={updateProfile.isPending}>
              <Plus className="mr-1 h-4 w-4" />
              Add
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Implicit weights */}
      <Card>
        <CardHeader>
          <CardTitle>Implicit Interests</CardTitle>
        </CardHeader>
        <CardContent>
          {implicitWeights.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No implicit data yet. Mark articles as read to build this list.
            </p>
          ) : (
            <div className="space-y-2">
              {implicitWeights.map(([category, weight]) => (
                <div key={category} className="flex items-center gap-3">
                  <span className="w-28 truncate text-sm capitalize">{category}</span>
                  <div className="flex-1 overflow-hidden rounded-full bg-muted">
                    <div
                      className="h-2 rounded-full bg-primary"
                      style={{ width: `${(weight * 100).toFixed(0)}%` }}
                    />
                  </div>
                  <span className="w-10 text-right text-xs text-muted-foreground">
                    {(weight * 100).toFixed(0)}%
                  </span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Trash2, Plus, Bell, BellOff, Tag, Clock } from "lucide-react";
import { toast } from "sonner";
import {
  useAlerts,
  useDeleteAlert,
  useProfile,
  useUpdateKeywords,
} from "@/lib/hooks";
import { KeywordsUpdateSchema, type KeywordsUpdate } from "@/lib/schemas";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { formatDate } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Delete confirmation dialog for alert history entries
// ---------------------------------------------------------------------------

interface DeleteAlertDialogProps {
  keyword: string;
  open: boolean;
  onCancel: () => void;
  onConfirm: () => void;
  loading: boolean;
}

function DeleteAlertDialog({
  keyword,
  open,
  onCancel,
  onConfirm,
  loading,
}: DeleteAlertDialogProps) {
  return (
    <Dialog open={open} onOpenChange={(v) => !v && onCancel()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Delete alert log entry?</DialogTitle>
          <DialogDescription>
            This will permanently remove the log entry for{" "}
            <span className="font-semibold">"{keyword}"</span>. The keyword
            watch rule on your profile will not be affected.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={onCancel} disabled={loading}>
            Cancel
          </Button>
          <Button variant="destructive" onClick={onConfirm} disabled={loading}>
            {loading ? "Deleting…" : "Delete"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ---------------------------------------------------------------------------
// Delete confirmation dialog for keyword watch rules
// ---------------------------------------------------------------------------

interface DeleteKeywordDialogProps {
  keyword: string;
  open: boolean;
  onCancel: () => void;
  onConfirm: () => void;
  loading: boolean;
}

function DeleteKeywordDialog({
  keyword,
  open,
  onCancel,
  onConfirm,
  loading,
}: DeleteKeywordDialogProps) {
  return (
    <Dialog open={open} onOpenChange={(v) => !v && onCancel()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Remove keyword watch?</DialogTitle>
          <DialogDescription>
            Removing <span className="font-semibold">"{keyword}"</span> will
            stop monitoring new articles for this term. Existing alert log
            entries are not affected.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={onCancel} disabled={loading}>
            Cancel
          </Button>
          <Button variant="destructive" onClick={onConfirm} disabled={loading}>
            {loading ? "Removing…" : "Remove"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function AlertsPage() {
  const { data: profile, isLoading: profileLoading } = useProfile();
  const { data: alerts, isLoading: alertsLoading } = useAlerts();
  const deleteAlert = useDeleteAlert();
  const updateKeywords = useUpdateKeywords();

  // Keyword add form
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<KeywordsUpdate>({
    resolver: zodResolver(KeywordsUpdateSchema),
  });

  // Delete alert log dialog state
  const [pendingDeleteAlert, setPendingDeleteAlert] = useState<{
    id: string;
    keyword: string;
  } | null>(null);

  // Delete keyword dialog state
  const [pendingDeleteKeyword, setPendingDeleteKeyword] = useState<string | null>(null);

  // ---------------------------------------------------------------------------
  // Keyword watch handlers
  // ---------------------------------------------------------------------------

  const onAddKeyword = async (data: KeywordsUpdate) => {
    const kw = data.keyword.toLowerCase().trim();
    const current = profile?.alert_keywords ?? [];
    if (current.includes(kw)) {
      toast.error(`"${kw}" is already in your watch list.`);
      return;
    }
    try {
      await updateKeywords.mutateAsync([...current, kw]);
      toast.success(`Watching "${kw}"`);
      reset();
    } catch {
      toast.error("Failed to add keyword. Please try again.");
    }
  };

  const confirmRemoveKeyword = async () => {
    if (!pendingDeleteKeyword || !profile) return;
    const next = profile.alert_keywords.filter((k) => k !== pendingDeleteKeyword);
    try {
      await updateKeywords.mutateAsync(next);
      toast.success(`Stopped watching "${pendingDeleteKeyword}"`);
    } catch {
      toast.error("Failed to remove keyword. Please try again.");
    } finally {
      setPendingDeleteKeyword(null);
    }
  };

  // ---------------------------------------------------------------------------
  // Alert log handlers
  // ---------------------------------------------------------------------------

  const confirmDeleteAlert = async () => {
    if (!pendingDeleteAlert) return;
    try {
      await deleteAlert.mutateAsync(pendingDeleteAlert.id);
      toast.success("Alert log entry deleted.");
    } catch {
      toast.error("Failed to delete alert. Please try again.");
    } finally {
      setPendingDeleteAlert(null);
    }
  };

  return (
    <div className="space-y-10">
      {/* ------------------------------------------------------------------ */}
      {/* Section 1 — Keyword Watches                                         */}
      {/* ------------------------------------------------------------------ */}
      <section className="space-y-4">
        <div>
          <h1 className="text-2xl font-bold">Alerts</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Add keywords below to monitor new articles. When a match is found,
            you will receive an email notification.
          </p>
        </div>

        <div className="rounded-lg border bg-card">
          <div className="flex items-center gap-2 border-b px-4 py-3">
            <Tag className="h-4 w-4 text-muted-foreground" />
            <h2 className="font-semibold">Active keyword watches</h2>
            {profile && (
              <Badge variant="secondary" className="ml-auto">
                {profile.alert_keywords.length} keyword
                {profile.alert_keywords.length !== 1 ? "s" : ""}
              </Badge>
            )}
          </div>

          {/* Add keyword form */}
          <form
            onSubmit={handleSubmit(onAddKeyword)}
            className="flex gap-2 border-b px-4 py-3"
          >
            <div className="flex-1">
              <Input
                {...register("keyword")}
                placeholder="e.g. python, climate, AI…"
                className="h-9"
              />
              {errors.keyword && (
                <p className="mt-1 text-xs text-destructive">
                  {errors.keyword.message}
                </p>
              )}
            </div>
            <Button
              type="submit"
              size="sm"
              disabled={isSubmitting || updateKeywords.isPending}
            >
              <Plus className="mr-1 h-4 w-4" />
              Add
            </Button>
          </form>

          {/* Keyword list */}
          <div className="divide-y">
            {profileLoading && (
              <p className="px-4 py-4 text-sm text-muted-foreground">
                Loading…
              </p>
            )}
            {!profileLoading && profile?.alert_keywords.length === 0 && (
              <div className="flex flex-col items-center gap-2 px-4 py-8 text-center text-muted-foreground">
                <BellOff className="h-8 w-8 opacity-40" />
                <p className="text-sm">
                  No keyword watches yet. Add one above to get notified.
                </p>
              </div>
            )}
            {profile?.alert_keywords.map((kw) => (
              <div
                key={kw}
                className="flex items-center justify-between px-4 py-3"
              >
                <div className="flex items-center gap-2">
                  <Bell className="h-4 w-4 text-primary" />
                  <span className="font-medium">{kw}</span>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setPendingDeleteKeyword(kw)}
                  aria-label={`Remove keyword ${kw}`}
                >
                  <Trash2 className="h-4 w-4 text-destructive" />
                </Button>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------------ */}
      {/* Section 2 — Alert History                                           */}
      {/* ------------------------------------------------------------------ */}
      <section className="space-y-4">
        <div className="rounded-lg border bg-card">
          <div className="flex items-center gap-2 border-b px-4 py-3">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <h2 className="font-semibold">Alert history</h2>
            <span className="ml-auto text-xs text-muted-foreground">
              Notifications fired by the background task
            </span>
          </div>

          <div className="divide-y">
            {alertsLoading && (
              <p className="px-4 py-4 text-sm text-muted-foreground">
                Loading…
              </p>
            )}
            {!alertsLoading && alerts?.length === 0 && (
              <div className="flex flex-col items-center gap-2 px-4 py-8 text-center text-muted-foreground">
                <Bell className="h-8 w-8 opacity-40" />
                <p className="text-sm">
                  No alerts have been fired yet. Alerts appear here when the
                  background task finds a matching article.
                </p>
              </div>
            )}
            {alerts?.map((alert) => (
              <div
                key={alert.id}
                className="flex items-center justify-between px-4 py-3"
              >
                <div className="flex flex-wrap items-center gap-3">
                  <span className="font-medium">{alert.trigger_keyword}</span>
                  <Badge variant="secondary">{alert.channel}</Badge>
                  {alert.sent_at && (
                    <span className="text-xs text-muted-foreground">
                      {formatDate(alert.sent_at)}
                    </span>
                  )}
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() =>
                    setPendingDeleteAlert({
                      id: alert.id,
                      keyword: alert.trigger_keyword,
                    })
                  }
                  aria-label="Delete alert log entry"
                >
                  <Trash2 className="h-4 w-4 text-destructive" />
                </Button>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------------ */}
      {/* Confirmation dialogs                                                */}
      {/* ------------------------------------------------------------------ */}
      <DeleteKeywordDialog
        keyword={pendingDeleteKeyword ?? ""}
        open={pendingDeleteKeyword !== null}
        onCancel={() => setPendingDeleteKeyword(null)}
        onConfirm={confirmRemoveKeyword}
        loading={updateKeywords.isPending}
      />

      <DeleteAlertDialog
        keyword={pendingDeleteAlert?.keyword ?? ""}
        open={pendingDeleteAlert !== null}
        onCancel={() => setPendingDeleteAlert(null)}
        onConfirm={confirmDeleteAlert}
        loading={deleteAlert.isPending}
      />
    </div>
  );
}

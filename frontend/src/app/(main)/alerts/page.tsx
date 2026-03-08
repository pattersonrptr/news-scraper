"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Trash2, Plus } from "lucide-react";
import { useAlerts, useCreateAlert, useDeleteAlert } from "@/lib/hooks";
import { AlertCreateSchema, type AlertCreate } from "@/lib/schemas";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { formatDate } from "@/lib/utils";

export default function AlertsPage() {
  const { data: alerts, isLoading } = useAlerts();
  const createAlert = useCreateAlert();
  const deleteAlert = useDeleteAlert();
  const [showForm, setShowForm] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<AlertCreate>({
    resolver: zodResolver(AlertCreateSchema),
    defaultValues: { channel: "email" },
  });

  const onSubmit = async (data: AlertCreate) => {
    await createAlert.mutateAsync(data);
    reset();
    setShowForm(false);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Alerts</h1>
        <Button size="sm" onClick={() => setShowForm((v) => !v)}>
          <Plus className="mr-2 h-4 w-4" />
          New alert
        </Button>
      </div>

      {showForm && (
        <form
          onSubmit={handleSubmit(onSubmit)}
          className="space-y-3 rounded-lg border bg-card p-4"
        >
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-sm font-medium">Keyword</label>
              <Input {...register("trigger_keyword")} placeholder="python, AI, climate…" />
              {errors.trigger_keyword && (
                <p className="text-xs text-destructive">{errors.trigger_keyword.message}</p>
              )}
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">Channel</label>
              <select
                {...register("channel")}
                className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
              >
                <option value="email">Email</option>
                <option value="telegram">Telegram</option>
                <option value="webhook">Webhook</option>
              </select>
            </div>
          </div>
          <div className="flex gap-2">
            <Button type="submit" size="sm" disabled={isSubmitting}>
              Save
            </Button>
            <Button type="button" variant="outline" size="sm" onClick={() => setShowForm(false)}>
              Cancel
            </Button>
          </div>
        </form>
      )}

      {isLoading && <p className="text-muted-foreground">Loading…</p>}

      {alerts?.length === 0 && !isLoading && (
        <p className="text-muted-foreground">No alerts yet. Add a keyword to get notified.</p>
      )}

      <div className="space-y-2">
        {alerts?.map((alert) => (
          <div
            key={alert.id}
            className="flex items-center justify-between rounded-lg border bg-card px-4 py-3"
          >
            <div className="flex flex-wrap items-center gap-3">
              <span className="font-medium">{alert.trigger_keyword}</span>
              <Badge variant="secondary">{alert.channel}</Badge>
              {alert.sent_at && (
                <span className="text-xs text-muted-foreground">
                  Last sent: {formatDate(alert.sent_at)}
                </span>
              )}
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => deleteAlert.mutate(alert.id)}
              aria-label="Delete alert"
            >
              <Trash2 className="h-4 w-4 text-destructive" />
            </Button>
          </div>
        ))}
      </div>
    </div>
  );
}

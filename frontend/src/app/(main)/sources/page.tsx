"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Trash2, Plus, Pencil, Check, X } from "lucide-react";
import { toast } from "sonner";
import {
  useSources,
  useCreateSource,
  useDeleteSource,
  useToggleSource,
  useUpdateSource,
} from "@/lib/hooks";
import {
  SourceCreateSchema,
  SourceUpdateSchema,
  type SourceCreate,
  type SourceUpdate,
  type Source,
} from "@/lib/schemas";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

// ---------------------------------------------------------------------------
// Edit row — inline form rendered inside the table row
// ---------------------------------------------------------------------------
function EditRow({
  source,
  onDone,
}: {
  source: Source;
  onDone: () => void;
}) {
  const updateSource = useUpdateSource();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<SourceUpdate>({
    resolver: zodResolver(SourceUpdateSchema),
    defaultValues: {
      name: source.name,
      url: source.url,
      feed_url: source.feed_url,
      language: source.language,
    },
  });

  const onSubmit = async (data: SourceUpdate) => {
    try {
      await updateSource.mutateAsync({ id: source.id, body: data });
      toast.success("Source updated successfully.");
      onDone();
    } catch {
      toast.error("Failed to update source.");
    }
  };

  return (
    <tr className="bg-muted/20">
      <td className="px-4 py-2" colSpan={4}>
        <form onSubmit={handleSubmit(onSubmit)} className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <Input {...register("name")} placeholder="Name" className="h-8 text-sm" />
            {errors.name && <p className="mt-0.5 text-xs text-destructive">{errors.name.message}</p>}
          </div>
          <div>
            <Input {...register("url")} placeholder="https://site.com" className="h-8 text-sm" />
            {errors.url && <p className="mt-0.5 text-xs text-destructive">{errors.url.message}</p>}
          </div>
          <div>
            <Input {...register("feed_url")} placeholder="https://site.com/rss" className="h-8 text-sm" />
            {errors.feed_url && <p className="mt-0.5 text-xs text-destructive">{errors.feed_url.message}</p>}
          </div>
          <div>
            <Input {...register("language")} placeholder="en" className="h-8 text-sm" />
          </div>
        </form>
      </td>
      <td className="px-4 py-2 text-right">
        <div className="flex justify-end gap-1">
          <Button
            size="icon"
            variant="ghost"
            className="h-8 w-8"
            onClick={handleSubmit(onSubmit)}
            disabled={isSubmitting}
            aria-label="Save"
          >
            <Check className="h-4 w-4 text-green-600" />
          </Button>
          <Button
            size="icon"
            variant="ghost"
            className="h-8 w-8"
            onClick={onDone}
            aria-label="Cancel"
          >
            <X className="h-4 w-4 text-muted-foreground" />
          </Button>
        </div>
      </td>
    </tr>
  );
}

// ---------------------------------------------------------------------------
// Delete confirmation dialog
// ---------------------------------------------------------------------------
function DeleteDialog({
  source,
  open,
  onOpenChange,
}: {
  source: Source | null;
  open: boolean;
  onOpenChange: (v: boolean) => void;
}) {
  const deleteSource = useDeleteSource();

  const handleDelete = async () => {
    if (!source) return;
    try {
      await deleteSource.mutateAsync(source.id);
      toast.success(`"${source.name}" removed.`);
      onOpenChange(false);
    } catch {
      toast.error("Failed to delete source.");
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Delete source</DialogTitle>
          <DialogDescription>
            Are you sure you want to delete{" "}
            <span className="font-semibold">{source?.name}</span>? This action cannot be undone.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={handleDelete}
            disabled={deleteSource.isPending}
          >
            {deleteSource.isPending ? "Deleting…" : "Delete"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ---------------------------------------------------------------------------
// Skeleton row — mirrors the real row layout while data is loading
// ---------------------------------------------------------------------------
function SourceRowSkeleton() {
  return (
    <tr>
      <td className="px-4 py-3"><Skeleton className="h-4 w-36" /></td>
      <td className="px-4 py-3"><Skeleton className="h-4 w-10" /></td>
      <td className="px-4 py-3"><Skeleton className="h-4 w-8" /></td>
      <td className="px-4 py-3"><Skeleton className="h-5 w-16 rounded-full" /></td>
      <td className="px-4 py-3 text-right">
        <div className="flex justify-end gap-1">
          <Skeleton className="h-8 w-8 rounded-md" />
          <Skeleton className="h-8 w-8 rounded-md" />
        </div>
      </td>
    </tr>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------
export default function SourcesPage() {
  const { data: sources, isLoading } = useSources();
  const createSource = useCreateSource();
  const toggleSource = useToggleSource();

  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [toDelete, setToDelete] = useState<Source | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<SourceCreate>({
    resolver: zodResolver(SourceCreateSchema),
    defaultValues: { source_type: "rss", language: "en", is_active: true },
  });

  const onSubmit = async (data: SourceCreate) => {
    try {
      await createSource.mutateAsync(data);
      toast.success("Source added successfully.");
      reset();
      setShowForm(false);
    } catch {
      toast.error("Failed to add source.");
    }
  };

  const handleToggle = async (source: Source) => {
    try {
      await toggleSource.mutateAsync({ id: source.id, is_active: !source.is_active });
      toast.success(
        `"${source.name}" ${!source.is_active ? "activated" : "deactivated"}.`
      );
    } catch {
      toast.error("Failed to update source status.");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Sources</h1>
        <Button size="sm" onClick={() => setShowForm((v) => !v)}>
          <Plus className="mr-2 h-4 w-4" />
          Add source
        </Button>
      </div>

      {/* Add source form */}
      {showForm && (
        <form
          onSubmit={handleSubmit(onSubmit)}
          className="space-y-3 rounded-lg border bg-card p-4"
        >
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-sm font-medium">Name</label>
              <Input {...register("name")} placeholder="Reuters" />
              {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">Homepage URL</label>
              <Input {...register("url")} placeholder="https://reuters.com" />
              {errors.url && <p className="text-xs text-destructive">{errors.url.message}</p>}
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">Feed URL</label>
              <Input
                {...register("feed_url")}
                placeholder="https://feeds.reuters.com/reuters/topNews"
              />
              {errors.feed_url && (
                <p className="text-xs text-destructive">{errors.feed_url.message}</p>
              )}
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">Language</label>
              <Input {...register("language")} placeholder="en" />
            </div>
          </div>
          <div className="flex gap-2">
            <Button type="submit" size="sm" disabled={isSubmitting}>
              Save
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setShowForm(false)}
            >
              Cancel
            </Button>
          </div>
        </form>
      )}

      {/* Sources table */}
      <div className="overflow-hidden rounded-lg border">
        <table className="w-full text-sm">
          <thead className="bg-muted/50">
            <tr>
              <th className="px-4 py-3 text-left font-medium">Name</th>
              <th className="px-4 py-3 text-left font-medium">Type</th>
              <th className="px-4 py-3 text-left font-medium">Language</th>
              <th className="px-4 py-3 text-left font-medium">Status</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody className="divide-y">
            {isLoading
              ? Array.from({ length: 5 }).map((_, i) => <SourceRowSkeleton key={i} />)
              : sources?.map((s) =>
              editingId === s.id ? (
                <EditRow key={s.id} source={s} onDone={() => setEditingId(null)} />
              ) : (
                <tr key={s.id} className="hover:bg-muted/25">
                  <td className="px-4 py-3">
                    <a
                      href={s.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-medium hover:underline"
                    >
                      {s.name}
                    </a>
                  </td>
                  <td className="px-4 py-3 uppercase text-muted-foreground">{s.source_type}</td>
                  <td className="px-4 py-3 text-muted-foreground">{s.language}</td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => handleToggle(s)}
                      disabled={toggleSource.isPending}
                      className="cursor-pointer disabled:opacity-50"
                      aria-label={s.is_active ? "Deactivate source" : "Activate source"}
                    >
                      <Badge variant={s.is_active ? "default" : "outline"}>
                        {s.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </button>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => setEditingId(s.id)}
                        aria-label="Edit source"
                      >
                        <Pencil className="h-4 w-4 text-muted-foreground" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => setToDelete(s)}
                        aria-label="Delete source"
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                  </td>
                </tr>
              )
            )}
          </tbody>
        </table>
      </div>

      {/* Delete confirmation dialog */}
      <DeleteDialog
        source={toDelete}
        open={toDelete !== null}
        onOpenChange={(v) => { if (!v) setToDelete(null); }}
      />
    </div>
  );
}

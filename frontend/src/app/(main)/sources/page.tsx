"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Trash2, Plus } from "lucide-react";
import { useSources, useCreateSource, useDeleteSource, useToggleSource } from "@/lib/hooks";
import { SourceCreateSchema, type SourceCreate } from "@/lib/schemas";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";

export default function SourcesPage() {
  const { data: sources, isLoading } = useSources();
  const createSource = useCreateSource();
  const deleteSource = useDeleteSource();
  const toggleSource = useToggleSource();
  const [showForm, setShowForm] = useState(false);

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
    await createSource.mutateAsync(data);
    reset();
    setShowForm(false);
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
              <Input {...register("feed_url")} placeholder="https://feeds.reuters.com/reuters/topNews" />
              {errors.feed_url && <p className="text-xs text-destructive">{errors.feed_url.message}</p>}
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
            <Button type="button" variant="outline" size="sm" onClick={() => setShowForm(false)}>
              Cancel
            </Button>
          </div>
        </form>
      )}

      {isLoading && <p className="text-muted-foreground">Loading…</p>}

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
            {sources?.map((s) => (
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
                    onClick={() => toggleSource.mutate({ id: s.id, is_active: !s.is_active })}
                    className="cursor-pointer"
                  >
                    <Badge variant={s.is_active ? "default" : "outline"}>
                      {s.is_active ? "Active" : "Inactive"}
                    </Badge>
                  </button>
                </td>
                <td className="px-4 py-3 text-right">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => deleteSource.mutate(s.id)}
                    aria-label="Delete source"
                  >
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

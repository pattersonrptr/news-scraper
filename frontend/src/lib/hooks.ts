/**
 * TanStack Query hooks for all API resources.
 */
"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  alertsApi,
  articlesApi,
  digestApi,
  profileApi,
  sourcesApi,
  trendsApi,
  type ArticleFilters,
} from "@/lib/api";
import {
  AlertCreateSchema,
  AlertSchema,
  ArticleListSchema,
  ArticleSchema,
  DigestPreviewSchema,
  ProfileSchema,
  ProfileUpdateSchema,
  KeywordsUpdateSchema,
  NotificationEmailUpdateSchema,
  SourceCreateSchema,
  SourceSchema,
  SourceUpdateSchema,
  TrendsSchema,
} from "@/lib/schemas";

// ---------------------------------------------------------------------------
// Articles
// ---------------------------------------------------------------------------

export function useArticles(filters?: ArticleFilters) {
  return useQuery({
    queryKey: ["articles", filters],
    queryFn: async () => {
      const raw = await articlesApi.list(filters);
      return ArticleListSchema.parse(raw);
    },
  });
}

export function useArticle(id: string | null) {
  return useQuery({
    queryKey: ["article", id],
    queryFn: async () => {
      const raw = await articlesApi.get(id!);
      return ArticleSchema.parse(raw);
    },
    enabled: id !== null,
  });
}

export function useMarkRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => articlesApi.markRead(id),
    onSuccess: (_data, id) => {
      qc.invalidateQueries({ queryKey: ["articles"] });
      qc.invalidateQueries({ queryKey: ["article", id] });
      // Backend now increments implicit_weights on read — refresh profile so
      // the Profile page chart updates without a manual reload.
      qc.invalidateQueries({ queryKey: ["profile"] });
    },
  });
}

// ---------------------------------------------------------------------------
// Sources
// ---------------------------------------------------------------------------

export function useSources() {
  return useQuery({
    queryKey: ["sources"],
    queryFn: async () => {
      const raw = await sourcesApi.list();
      return (raw as unknown[]).map((r) => SourceSchema.parse(r));
    },
  });
}

export function useCreateSource() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: unknown) => sourcesApi.create(body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sources"] }),
    meta: { schema: SourceCreateSchema },
  });
}

export function useUpdateSource() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: unknown }) =>
      sourcesApi.update(id, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sources"] }),
    meta: { schema: SourceUpdateSchema },
  });
}

export function useDeleteSource() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => sourcesApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sources"] }),
  });
}

export function useToggleSource() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      sourcesApi.toggle(id, is_active),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sources"] }),
  });
}

// ---------------------------------------------------------------------------
// Profile
// ---------------------------------------------------------------------------

export function useProfile() {
  return useQuery({
    queryKey: ["profile"],
    queryFn: async () => {
      const raw = await profileApi.get();
      return ProfileSchema.parse(raw);
    },
  });
}

export function useUpdateProfile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (interests: string[]) => profileApi.updateInterests(interests),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["profile"] }),
    meta: { schema: ProfileUpdateSchema },
  });
}

export function useUpdateKeywords() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (keywords: string[]) => profileApi.updateKeywords(keywords),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["profile"] }),
    meta: { schema: KeywordsUpdateSchema },
  });
}

export function useUpdateNotificationEmail() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (email: string) => profileApi.updateNotificationEmail(email),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["profile"] }),
    meta: { schema: NotificationEmailUpdateSchema },
  });
}

// ---------------------------------------------------------------------------
// Alerts
// ---------------------------------------------------------------------------

export function useAlerts(limit = 50) {
  return useQuery({
    queryKey: ["alerts", limit],
    queryFn: async () => {
      const raw = await alertsApi.list(limit);
      return (raw as unknown[]).map((r) => AlertSchema.parse(r));
    },
  });
}

export function useCreateAlert() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: unknown) => alertsApi.create(body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["alerts"] }),
    meta: { schema: AlertCreateSchema },
  });
}

export function useDeleteAlert() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => alertsApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["alerts"] }),
  });
}

// ---------------------------------------------------------------------------
// Trends
// ---------------------------------------------------------------------------

export function useTrends(hours = 24) {
  return useQuery({
    queryKey: ["trends", hours],
    queryFn: async () => {
      const raw = await trendsApi.get(hours);
      return TrendsSchema.parse(raw);
    },
    refetchInterval: 60_000,
  });
}

// ---------------------------------------------------------------------------
// Digest preview
// ---------------------------------------------------------------------------

export function useDigestPreview(hours = 24) {
  return useQuery({
    queryKey: ["digest-preview", hours],
    queryFn: async () => {
      const raw = await digestApi.preview(hours);
      return DigestPreviewSchema.parse(raw);
    },
  });
}

/**
 * Zod schemas mirroring the FastAPI response shapes.
 * Used for runtime validation and TypeScript inference.
 */
import { z } from "zod";

// ---------------------------------------------------------------------------
// Common
// ---------------------------------------------------------------------------

export const PaginatedMeta = z.object({
  page: z.number(),
  page_size: z.number(),
  total: z.number(),
  pages: z.number(),
});

// ---------------------------------------------------------------------------
// Article
// ---------------------------------------------------------------------------

export const ArticleSchema = z.object({
  id: z.string().uuid(),
  url: z.string().url(),
  title: z.string(),
  summary: z.string().nullable(),
  body: z.string().nullable().optional(),
  language: z.string().nullable(),
  sentiment: z.number().int(),
  sentiment_score: z.number().optional().default(0),
  category: z.string().nullable(),
  relevance_score: z.number().optional().default(0),
  is_processed: z.boolean().optional().default(false),
  is_read: z.boolean().optional().default(false),
  published_at: z.string().nullable(),
  collected_at: z.string(),
  entities: z.record(z.unknown()).nullable().optional(),
  source_id: z.string().uuid().nullable().optional(),
});

export const ArticleListSchema = z.object({
  items: z.array(ArticleSchema),
  total: z.number(),
  limit: z.number(),
  offset: z.number(),
});

export type Article = z.infer<typeof ArticleSchema>;
export type ArticleList = z.infer<typeof ArticleListSchema>;

// ---------------------------------------------------------------------------
// Source
// ---------------------------------------------------------------------------

export const SourceSchema = z.object({
  id: z.string().uuid(),
  name: z.string(),
  url: z.string().url(),
  feed_url: z.string().url(),
  source_type: z.enum(["rss", "html", "api"]),
  language: z.string(),
  is_active: z.boolean(),
  created_at: z.string().optional(),
});

export const SourceCreateSchema = z.object({
  name: z.string().min(1).max(200),
  url: z.string().url(),
  feed_url: z.string().url(),
  source_type: z.enum(["rss", "html", "api"]).default("rss"),
  language: z.string().min(2).max(10).default("en"),
  is_active: z.boolean().default(true),
});

export const SourceUpdateSchema = z.object({
  name: z.string().min(1).max(200).optional(),
  url: z.string().url().optional(),
  feed_url: z.string().url().optional(),
  language: z.string().min(2).max(10).optional(),
  fetch_interval: z.number().int().min(1).optional(),
  is_active: z.boolean().optional(),
});

export type Source = z.infer<typeof SourceSchema>;
export type SourceCreate = z.infer<typeof SourceCreateSchema>;
export type SourceUpdate = z.infer<typeof SourceUpdateSchema>;

// ---------------------------------------------------------------------------
// Profile
// ---------------------------------------------------------------------------

export const ProfileSchema = z.object({
  id: z.string().uuid(),
  explicit_interests: z.array(z.string()),
  implicit_weights: z.record(z.number()),
  preferred_language: z.string().nullable().optional(),
  digest_enabled: z.boolean().optional(),
  digest_hour: z.number().int().optional(),
});

export const ProfileUpdateSchema = z.object({
  explicit_interests: z.array(z.string()),
});

export type Profile = z.infer<typeof ProfileSchema>;
export type ProfileUpdate = z.infer<typeof ProfileUpdateSchema>;

// ---------------------------------------------------------------------------
// Alert
// ---------------------------------------------------------------------------

export const AlertSchema = z.object({
  id: z.string().uuid(),
  user_id: z.string().uuid().nullable(),
  article_id: z.string().uuid().nullable(),
  trigger_keyword: z.string(),
  channel: z.string(),
  sent_at: z.string().nullable(),
});

export const AlertCreateSchema = z.object({
  trigger_keyword: z.string().min(1).max(200),
  channel: z.enum(["email", "telegram", "webhook"]).default("email"),
  article_id: z.string().uuid().optional(),
});

export type Alert = z.infer<typeof AlertSchema>;
export type AlertCreate = z.infer<typeof AlertCreateSchema>;

// ---------------------------------------------------------------------------
// Trends
// ---------------------------------------------------------------------------

export const TrendsSchema = z.object({
  total_articles: z.number(),
  top_categories: z.array(z.tuple([z.string(), z.number()])),
  top_keywords: z.array(z.tuple([z.string(), z.number()])),
  sentiment_distribution: z.record(z.number()),
  computed_at: z.string(),
});

export type Trends = z.infer<typeof TrendsSchema>;

// ---------------------------------------------------------------------------
// Digest preview
// ---------------------------------------------------------------------------

export const DigestArticleSchema = z.object({
  id: z.string(),
  title: z.string(),
  url: z.string(),
  summary: z.string().nullable(),
  sentiment: z.number(),
  category: z.string().nullable(),
  relevance_score: z.number().nullable(),
  published_at: z.string().nullable(),
});

export const DigestPreviewSchema = z.object({
  total_articles: z.number(),
  date_label: z.string(),
  generated_at: z.string(),
  top_categories: z.array(z.tuple([z.string(), z.number()])),
  sentiment_distribution: z.record(z.number()),
  sections: z.record(z.array(DigestArticleSchema)),
});

export type DigestPreview = z.infer<typeof DigestPreviewSchema>;

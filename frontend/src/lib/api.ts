/**
 * Base API client.  All server-side and client-side calls go through here.
 * During development, Next.js rewrites /api/v1/* → FastAPI (see next.config.ts).
 */

const BASE =
  typeof window === "undefined"
    ? // Server-side (SSR / RSC): call backend directly
      (process.env.BACKEND_URL ?? "http://localhost:8000") + "/api/v1"
    : // Client-side: use the relative rewrite path
      "/api/v1";

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });

  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new ApiError(res.status, text);
  }

  // 204 No Content
  if (res.status === 204) return undefined as T;

  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Articles
// ---------------------------------------------------------------------------

export type ArticleFilters = {
  page?: number;
  page_size?: number;
  source_id?: string;
  category?: string;
  sentiment?: number;
  from_date?: string;
  to_date?: string;
};

export const articlesApi = {
  list: (filters?: ArticleFilters) => {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([k, v]) => {
        if (v !== undefined && v !== "") params.set(k, String(v));
      });
    }
    const qs = params.toString();
    return request<unknown>(`/articles${qs ? `?${qs}` : ""}`);
  },
  get: (id: string) => request<unknown>(`/articles/${id}`),
  markRead: (id: string) =>
    request<unknown>(`/articles/${id}/read`, { method: "PATCH" }),
};

// ---------------------------------------------------------------------------
// Sources
// ---------------------------------------------------------------------------

export const sourcesApi = {
  list: () => request<unknown[]>("/sources"),
  create: (body: unknown) =>
    request<unknown>("/sources", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  delete: (id: string) =>
    request<void>(`/sources/${id}`, { method: "DELETE" }),
  toggle: (id: string, is_active: boolean) =>
    request<unknown>(`/sources/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ is_active }),
    }),
};

// ---------------------------------------------------------------------------
// Profile
// ---------------------------------------------------------------------------

export const profileApi = {
  get: () => request<unknown>("/profile"),
  updateInterests: (interests: string[]) =>
    request<unknown>("/profile/interests", {
      method: "PUT",
      body: JSON.stringify({ explicit_interests: interests }),
    }),
};

// ---------------------------------------------------------------------------
// Alerts
// ---------------------------------------------------------------------------

export const alertsApi = {
  list: (limit = 50) => request<unknown[]>(`/alerts?limit=${limit}`),
  create: (body: unknown) =>
    request<unknown>("/alerts", { method: "POST", body: JSON.stringify(body) }),
  delete: (id: string) =>
    request<void>(`/alerts/${id}`, { method: "DELETE" }),
};

// ---------------------------------------------------------------------------
// Trends & Digest
// ---------------------------------------------------------------------------

export const trendsApi = {
  get: (hours = 24) => request<unknown>(`/trends?hours=${hours}`),
};

export const digestApi = {
  preview: (hours = 24) => request<unknown>(`/digest/preview?hours=${hours}`),
};

export { ApiError };

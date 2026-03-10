/**
 * Base API client.  All server-side and client-side calls go through here.
 * During development, Next.js rewrites /api/v1/* → FastAPI (see next.config.ts).
 *
 * When running in the browser the stored access token is attached as an
 * `Authorization: Bearer <token>` header on every request.
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

/** Read the stored JWT from localStorage (browser only). */
function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem("news-scraper-auth");
    if (!raw) return null;
    const parsed = JSON.parse(raw) as { state?: { token?: string } };
    return parsed?.state?.token ?? null;
  } catch {
    return null;
  }
}

/** Read the stored refresh token from localStorage (browser only). */
function getStoredRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem("news-scraper-auth");
    if (!raw) return null;
    const parsed = JSON.parse(raw) as { state?: { refresh_token?: string } };
    return parsed?.state?.refresh_token ?? null;
  } catch {
    return null;
  }
}

/** Attempt a silent token refresh. Returns the new access token or null. */
async function silentRefresh(): Promise<string | null> {
  const refresh_token = getStoredRefreshToken();
  if (!refresh_token) return null;
  try {
    const res = await fetch(`${BASE}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token }),
    });
    if (!res.ok) return null;
    const data = (await res.json()) as { access_token: string; refresh_token: string };
    // Patch localStorage directly so Zustand picks it up on next read
    const raw = localStorage.getItem("news-scraper-auth");
    if (raw) {
      const parsed = JSON.parse(raw) as { state?: Record<string, unknown> };
      if (parsed.state) {
        parsed.state.token = data.access_token;
        parsed.state.refresh_token = data.refresh_token;
        localStorage.setItem("news-scraper-auth", JSON.stringify(parsed));
      }
    }
    return data.access_token;
  } catch {
    return null;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getStoredToken();
  const authHeader: Record<string, string> = token
    ? { Authorization: `Bearer ${token}` }
    : {};

  const res = await fetch(`${BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...authHeader,
      ...init?.headers,
    },
    ...init,
  });

  // On 401, attempt a silent token refresh and retry once
  if (res.status === 401) {
    const newToken = await silentRefresh();
    if (newToken) {
      const retryRes = await fetch(`${BASE}${path}`, {
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${newToken}`,
          ...init?.headers,
        },
        ...init,
      });
      if (!retryRes.ok) {
        const text = await retryRes.text().catch(() => retryRes.statusText);
        throw new ApiError(retryRes.status, text);
      }
      if (retryRes.status === 204) return undefined as T;
      return retryRes.json() as Promise<T>;
    }
    // Refresh failed — clear auth and redirect to login
    localStorage.removeItem("news-scraper-auth");
    if (typeof window !== "undefined") window.location.href = "/login";
    throw new ApiError(401, "Session expired. Please log in again.");
  }

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
  limit?: number;
  offset?: number;
  source_id?: string;
  category?: string;
  sentiment?: number;
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
  update: (id: string, body: unknown) =>
    request<unknown>(`/sources/${id}`, {
      method: "PUT",
      body: JSON.stringify(body),
    }),
  delete: (id: string) =>
    request<void>(`/sources/${id}`, { method: "DELETE" }),
  toggle: (id: string, is_active: boolean) =>
    request<unknown>(`/sources/${id}`, {
      method: "PUT",
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
  updateKeywords: (keywords: string[]) =>
    request<unknown>("/profile/interests", {
      method: "PUT",
      body: JSON.stringify({ alert_keywords: keywords }),
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

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface MeResponse {
  id: string;
  email: string;
  display_name: string;
  is_active: boolean;
}

export const authApi = {
  register: (email: string, password: string, display_name?: string) =>
    request<MeResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, display_name: display_name ?? "" }),
    }),

  /** OAuth2 password flow — username field carries the e-mail. */
  login: (email: string, password: string) => {
    const form = new URLSearchParams();
    form.set("username", email);
    form.set("password", password);
    return fetch(`${BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form.toString(),
    }).then(async (res) => {
      if (!res.ok) {
        const text = await res.text().catch(() => res.statusText);
        throw new ApiError(res.status, text);
      }
      return res.json() as Promise<TokenResponse>;
    });
  },

  refresh: (refresh_token: string) =>
    request<TokenResponse>("/auth/refresh", {
      method: "POST",
      body: JSON.stringify({ refresh_token }),
    }),

  me: () => request<MeResponse>("/auth/me"),

  logout: () => request<void>("/auth/logout", { method: "POST" }),
};

export { ApiError };

/**
 * Global auth state managed by Zustand.
 *
 * The access token is persisted in localStorage so that the user stays logged
 * in across page refreshes.  The token is loaded back into memory on hydration
 * by the AuthProvider component (see providers.tsx).
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface AuthUser {
  id: string;
  email: string;
  display_name: string;
}

interface AuthState {
  /** JWT access token or null when not authenticated. */
  token: string | null;
  /** JWT refresh token or null when not authenticated. */
  refresh_token: string | null;
  user: AuthUser | null;
  /** Store the token + user after a successful login/register. */
  setAuth: (token: string, refresh_token: string, user: AuthUser) => void;
  /** Clear all auth state (logout). */
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      refresh_token: null,
      user: null,
      setAuth: (token, refresh_token, user) => set({ token, refresh_token, user }),
      clearAuth: () => set({ token: null, refresh_token: null, user: null }),
    }),
    {
      name: "news-scraper-auth", // localStorage key
      partialize: (state) => ({ token: state.token, refresh_token: state.refresh_token, user: state.user }),
    },
  ),
);

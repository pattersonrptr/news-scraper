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
  user: AuthUser | null;
  /** Store the token + user after a successful login/register. */
  setAuth: (token: string, user: AuthUser) => void;
  /** Clear all auth state (logout). */
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      setAuth: (token, user) => set({ token, user }),
      clearAuth: () => set({ token: null, user: null }),
    }),
    {
      name: "news-scraper-auth", // localStorage key
      // Only persist the token — re-fetch user from /auth/me on hydration
      partialize: (state) => ({ token: state.token, user: state.user }),
    },
  ),
);

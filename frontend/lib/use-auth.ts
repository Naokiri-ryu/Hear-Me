"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiError, clearToken, getMe, getToken, type UserOut } from "@/lib/api";

export const AUTH_EVENT = "hm:auth-change";

export interface AuthState {
  user: UserOut | null;
  loading: boolean;
  logout: () => void;
}

/** Client-side auth state, synced across components/tabs via window events. */
export function useAuth(): AuthState {
  const [user, setUser] = useState<UserOut | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    const token = getToken();
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const me = await getMe();
      setUser(me);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        clearToken();
      }
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    clearToken();
    setUser(null);
    setLoading(false);
    window.dispatchEvent(new Event(AUTH_EVENT));
  }, []);

  useEffect(() => {
    const initial = window.setTimeout(() => void refresh(), 0);
    window.addEventListener(AUTH_EVENT, refresh);
    window.addEventListener("storage", refresh);
    return () => {
      window.clearTimeout(initial);
      window.removeEventListener(AUTH_EVENT, refresh);
      window.removeEventListener("storage", refresh);
    };
  }, [refresh]);

  return { user, loading, logout };
}
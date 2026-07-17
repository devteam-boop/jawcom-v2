import { useCallback, useState } from "react";
import { authService } from "@/services/auth";

const STORAGE_KEY = "jawcom.agent.session";

function readToken() {
  try {
    return sessionStorage.getItem(STORAGE_KEY) || null;
  } catch {
    return null;
  }
}

/**
 * Minimal agent session — see backend/app/core/session_auth.py for the
 * full rationale (shared-workspace passcode, not multi-user auth). Token
 * lives in sessionStorage only (cleared when the tab closes) and is never
 * sent anywhere except POST /api/messages/* (see messages.js).
 */
export function useAgentSession() {
  const [token, setToken] = useState(readToken);

  const login = useCallback(async (password) => {
    const result = await authService.login(password);
    try {
      sessionStorage.setItem(STORAGE_KEY, result.token);
    } catch {
      // sessionStorage unavailable (private mode) — token still works for
      // this render, just won't survive a reload.
    }
    setToken(result.token);
    return result.token;
  }, []);

  const logout = useCallback(() => {
    try {
      sessionStorage.removeItem(STORAGE_KEY);
    } catch {
      // ignore
    }
    setToken(null);
  }, []);

  return { token, login, logout };
}

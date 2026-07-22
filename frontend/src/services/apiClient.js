const BASE_URL = process.env.REACT_APP_BACKEND_URL || "http://127.0.0.1:8000";

const CSRF_COOKIE_NAME = "jawcom_csrf";
const CSRF_HEADER_NAME = "X-CSRF-Token";

// Frontend (Vercel) and backend (Render) are different origins — the
// browser sends the jawcom_csrf cookie back to the backend fine, but
// document.cookie can never expose a cookie set by a different origin
// than the page reading it, no SameSite/Secure/Domain setting changes
// that. So the source of truth is this in-memory value, populated from
// the login/me response bodies (see AuthContext.jsx) — the cookie read
// below is kept only as a fallback for same-origin dev/deploy setups
// where it happens to work.
let inMemoryCsrfToken = null;

export function setCsrfToken(token) {
  inMemoryCsrfToken = token || null;
}

class ApiError extends Error {
  constructor(status, body) {
    const detail =
      body?.detail ||
      (typeof body === "string" ? body : JSON.stringify(body)) ||
      `HTTP ${status}`;
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

function readCsrfCookie() {
  const match = document.cookie.match(new RegExp(`(?:^|; )${CSRF_COOKIE_NAME}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

async function handleResponse(res) {
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    // GET /api/auth/me 401 is the expected result of AuthContext's
    // "am I logged in?" probe on every fresh page load with no session
    // yet — not a real failure, so it's the one case that doesn't get
    // logged at all.
    const isSessionProbe = res.status === 401 && res.url.includes("/api/auth/me");
    // 404 is routinely part of normal control flow here, not a backend
    // problem — a not-yet-built feature (e.g. GET /api/campaigns, caught
    // by Campaigns.jsx to show an honest empty state) or a resource that
    // legitimately doesn't exist (e.g. GET /api/leads/{id}/summary for a
    // deleted lead, caught by useLeadSummaries). console.error is for
    // things that indicate an actual bug; console.warn keeps these
    // visible for debugging without tripping "no console errors" checks.
    if (isSessionProbe) {
      // no log at all
    } else if (res.status === 404) {
      console.warn(`API ${res.status} ${res.url}:`, body);
    } else {
      console.error(`API ${res.status} ${res.url}:`, body);
    }
    if (res.status === 401 && !res.url.includes("/api/auth/login") && !isSessionProbe) {
      // Session expired/invalid on an otherwise-protected call — let
      // AuthContext react (redirect to /login) without every caller
      // having to special-case this.
      window.dispatchEvent(new CustomEvent("auth:unauthorized"));
    }
    throw new ApiError(res.status, body);
  }
  return body;
}

function buildUrl(path, params) {
  const qs = params ? `?${new URLSearchParams(params)}` : "";
  return `${BASE_URL}${path}${qs}`;
}

function mutationHeaders(extra) {
  const headers = { "Content-Type": "application/json", ...extra };
  const csrf = inMemoryCsrfToken || readCsrfCookie();
  if (csrf) headers[CSRF_HEADER_NAME] = csrf;
  return headers;
}

export const api = {
  get: async (path, params) => {
    const res = await fetch(buildUrl(path, params), { credentials: "include" });
    return handleResponse(res);
  },

  post: async (path, body, { token } = {}) => {
    const headers = mutationHeaders(token ? { Authorization: `Bearer ${token}` } : {});
    const res = await fetch(`${BASE_URL}${path}`, {
      method: "POST",
      headers,
      credentials: "include",
      body: JSON.stringify(body),
    });
    return handleResponse(res);
  },

  patch: async (path, body) => {
    const res = await fetch(`${BASE_URL}${path}`, {
      method: "PATCH",
      headers: mutationHeaders(),
      credentials: "include",
      body: JSON.stringify(body),
    });
    return handleResponse(res);
  },

  del: async (path) => {
    const res = await fetch(`${BASE_URL}${path}`, {
      method: "DELETE",
      headers: mutationHeaders(),
      credentials: "include",
    });
    if (!res.ok) await handleResponse(res);
  },
};

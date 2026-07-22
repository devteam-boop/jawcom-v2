const BASE_URL = process.env.REACT_APP_BACKEND_URL || "http://127.0.0.1:8000";

const CSRF_COOKIE_NAME = "jawcom_csrf";
const CSRF_HEADER_NAME = "X-CSRF-Token";

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
    console.error(`API ${res.status} ${res.url}:`, body);
    if (res.status === 401 && !res.url.includes("/api/auth/login")) {
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
  const csrf = readCsrfCookie();
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

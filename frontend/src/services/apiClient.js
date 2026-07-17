const BASE_URL = process.env.REACT_APP_BACKEND_URL || "http://127.0.0.1:8000";

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

async function handleResponse(res) {
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    console.error(`API ${res.status} ${res.url}:`, body);
    throw new ApiError(res.status, body);
  }
  return body;
}

function buildUrl(path, params) {
  const qs = params ? `?${new URLSearchParams(params)}` : "";
  return `${BASE_URL}${path}${qs}`;
}

export const api = {
  get: async (path, params) => {
    const res = await fetch(buildUrl(path, params));
    return handleResponse(res);
  },

  post: async (path, body, { token } = {}) => {
    const headers = { "Content-Type": "application/json" };
    if (token) headers.Authorization = `Bearer ${token}`;
    const res = await fetch(`${BASE_URL}${path}`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
    });
    return handleResponse(res);
  },

  patch: async (path, body) => {
    const res = await fetch(`${BASE_URL}${path}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return handleResponse(res);
  },

  del: async (path) => {
    const res = await fetch(`${BASE_URL}${path}`, { method: "DELETE" });
    if (!res.ok) await handleResponse(res);
  },
};

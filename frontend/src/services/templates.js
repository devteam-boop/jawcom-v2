const BASE = "/api/templates";

export const templateService = {
  list: async (filters = {}) => {
    const params = new URLSearchParams(filters);
    const res = await fetch(`${BASE}?${params}`);
    if (!res.ok) throw new Error("Failed to list templates");
    return res.json();
  },
  get: async (id) => {
    const res = await fetch(`${BASE}/${id}`);
    if (!res.ok) throw new Error("Failed to get template");
    return res.json();
  },
  create: async (payload) => {
    const res = await fetch(BASE, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error("Failed to create template");
    return res.json();
  },
  update: async (id, payload) => {
    const res = await fetch(`${BASE}/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error("Failed to update template");
    return res.json();
  },
  getUsage: async (id) => {
    const res = await fetch(`${BASE}/${id}/usage`);
    if (!res.ok) throw new Error("Failed to get template usage");
    return res.json();
  },
};

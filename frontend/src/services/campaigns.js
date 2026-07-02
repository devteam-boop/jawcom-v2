const BASE = "/api/campaigns";

export const campaignService = {
  list: async () => {
    const res = await fetch(BASE);
    if (!res.ok) throw new Error("Failed to list campaigns");
    return res.json();
  },
  get: async (id) => {
    const res = await fetch(`${BASE}/${id}`);
    if (!res.ok) throw new Error("Failed to get campaign");
    return res.json();
  },
  create: async (payload) => {
    const res = await fetch(BASE, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error("Failed to create campaign");
    return res.json();
  },
  update: async (id, payload) => {
    const res = await fetch(`${BASE}/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error("Failed to update campaign");
    return res.json();
  },
  launch: async (id) => {
    const res = await fetch(`${BASE}/${id}/launch`, { method: "POST" });
    if (!res.ok) throw new Error("Failed to launch campaign");
    return res.json();
  },
  pause: async (id) => {
    const res = await fetch(`${BASE}/${id}/pause`, { method: "POST" });
    if (!res.ok) throw new Error("Failed to pause campaign");
    return res.json();
  },
};

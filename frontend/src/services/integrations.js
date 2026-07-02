const BASE = "/api/integrations";

export const integrationService = {
  list: async () => {
    const res = await fetch(BASE);
    if (!res.ok) throw new Error("Failed to list integrations");
    return res.json();
  },
  get: async (id) => {
    const res = await fetch(`${BASE}/${id}`);
    if (!res.ok) throw new Error("Failed to get integration");
    return res.json();
  },
  connect: async (id, config) => {
    const res = await fetch(`${BASE}/${id}/connect`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config),
    });
    if (!res.ok) throw new Error("Failed to connect integration");
    return res.json();
  },
  disconnect: async (id) => {
    const res = await fetch(`${BASE}/${id}/disconnect`, { method: "POST" });
    if (!res.ok) throw new Error("Failed to disconnect integration");
    return res.json();
  },
};

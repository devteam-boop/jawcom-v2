const BASE = "/api/journeys";

export const journeyService = {
  list: async () => {
    const res = await fetch(BASE);
    if (!res.ok) throw new Error("Failed to list journeys");
    return res.json();
  },
  get: async (id) => {
    const res = await fetch(`${BASE}/${id}`);
    if (!res.ok) throw new Error("Failed to get journey");
    return res.json();
  },
  create: async (payload) => {
    const res = await fetch(BASE, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error("Failed to create journey");
    return res.json();
  },
  update: async (id, payload) => {
    const res = await fetch(`${BASE}/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error("Failed to update journey");
    return res.json();
  },
  delete: async (id) => {
    const res = await fetch(`${BASE}/${id}`, { method: "DELETE" });
    if (!res.ok) throw new Error("Failed to delete journey");
    return res.json();
  },
  getFlow: async (id) => {
    const res = await fetch(`${BASE}/${id}/flow`);
    if (!res.ok) throw new Error("Failed to get flow definition");
    return res.json();
  },
  saveFlow: async (id, flowDefinition) => {
    const res = await fetch(`${BASE}/${id}/flow`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(flowDefinition),
    });
    if (!res.ok) throw new Error("Failed to save flow definition");
    return res.json();
  },
  getRunningInstances: async (id) => {
    const res = await fetch(`${BASE}/${id}/instances`);
    if (!res.ok) throw new Error("Failed to get running instances");
    return res.json();
  },
  getStageMappings: async (id) => {
    const res = await fetch(`${BASE}/${id}/stage-mappings`);
    if (!res.ok) throw new Error("Failed to get stage mappings");
    return res.json();
  },
  updateStageMappings: async (id, mappings) => {
    const res = await fetch(`${BASE}/${id}/stage-mappings`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(mappings),
    });
    if (!res.ok) throw new Error("Failed to update stage mappings");
    return res.json();
  },
};

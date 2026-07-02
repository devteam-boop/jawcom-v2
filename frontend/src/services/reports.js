const BASE = "/api/reports";

export const reportService = {
  delivery: async (filters = {}) => {
    const params = new URLSearchParams(filters);
    const res = await fetch(`${BASE}/delivery?${params}`);
    if (!res.ok) throw new Error("Failed to get delivery report");
    return res.json();
  },
  journeyAnalytics: async (journeyId) => {
    const res = await fetch(`${BASE}/journeys/${journeyId}`);
    if (!res.ok) throw new Error("Failed to get journey analytics");
    return res.json();
  },
  campaignAnalytics: async (campaignId) => {
    const res = await fetch(`${BASE}/campaigns/${campaignId}`);
    if (!res.ok) throw new Error("Failed to get campaign analytics");
    return res.json();
  },
  summary: async () => {
    const res = await fetch(`${BASE}/summary`);
    if (!res.ok) throw new Error("Failed to get report summary");
    return res.json();
  },
};

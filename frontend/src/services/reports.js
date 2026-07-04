import { api } from "./apiClient";

export const reportService = {
  delivery: async (filters = {}) => api.get("/api/reports/delivery", filters),
  journeyAnalytics: async (journeyId) => api.get(`/api/reports/journeys/${journeyId}`),
  campaignAnalytics: async (campaignId) => api.get(`/api/reports/campaigns/${campaignId}`),
  summary: async () => api.get("/api/reports/summary"),
};

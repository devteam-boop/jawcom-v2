import { api } from "./apiClient";

export const aiSummaryService = {
  get: async (leadId) => api.get(`/api/leads/${leadId}/ai-summary`),
};

import { api } from "./apiClient";

export const aiAssistantService = {
  get: async (leadId) => api.get(`/api/leads/${leadId}/ai-assistant`),
};

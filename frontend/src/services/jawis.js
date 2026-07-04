import { api } from "./apiClient";

export const jawisService = {
  getLead: async (leadId) => api.get(`/api/jawis/leads/${leadId}`),
  getCompany: async (companyId) => api.get(`/api/jawis/companies/${companyId}`),
  getLeadStage: async (leadId) => api.get(`/api/jawis/leads/${leadId}/stage`),
  searchLeads: async (query) => api.get("/api/jawis/leads", { q: query }),
};

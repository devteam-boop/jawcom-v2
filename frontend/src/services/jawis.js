import { api } from "./apiClient";

// getLead uses the real, live GET /api/leads/{id}/summary (a thin proxy
// over the existing JawisClient.get_lead() already used server-side by
// message sends — added in Phase 2). getCompany/getLeadStage/searchLeads
// still target /api/jawis/* routes that were never registered in
// backend/app/main.py — left as-is, not part of Phase 2 scope.
export const jawisService = {
  getLead: async (leadId) => api.get(`/api/leads/${leadId}/summary`),
  getCompany: async (companyId) => api.get(`/api/jawis/companies/${companyId}`),
  getLeadStage: async (leadId) => api.get(`/api/jawis/leads/${leadId}/stage`),
  searchLeads: async (query) => api.get("/api/jawis/leads", { q: query }),
};

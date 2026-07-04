import { api } from "./apiClient";

export const runningInstanceService = {
  list: async ({ skip = 0, limit = 100, journeyId, status, leadId } = {}) => {
    const params = { skip, limit };
    if (journeyId) params.journey_id = journeyId;
    if (status) params.status = status;
    if (leadId) params.lead_id = leadId;
    return api.get("/api/running-instances", params);
  },

  get: async (id) => api.get(`/api/running-instances/${id}`),

  create: async (payload) => api.post("/api/running-instances", payload),

  update: async (id, payload) => api.patch(`/api/running-instances/${id}`, payload),

  delete: async (id) => api.del(`/api/running-instances/${id}`),

  complete: async (id) => api.post(`/api/running-instances/${id}/complete`),

  fail: async (id) => api.post(`/api/running-instances/${id}/fail`),
};

import { api } from "./apiClient";

export const campaignService = {
  list: async () => api.get("/api/campaigns"),
  get: async (id) => api.get(`/api/campaigns/${id}`),
  create: async (payload) => api.post("/api/campaigns", payload),
  update: async (id, payload) => api.patch(`/api/campaigns/${id}`, payload),
  launch: async (id) => api.post(`/api/campaigns/${id}/launch`),
  pause: async (id) => api.post(`/api/campaigns/${id}/pause`),
};

import { api } from "./apiClient";

export const journeyService = {
  list: async ({ skip = 0, limit = 100, status } = {}) => {
    const params = { skip, limit };
    if (status) params.status = status;
    return api.get("/api/journeys", params);
  },

  get: async (id) => api.get(`/api/journeys/${id}`),

  create: async (payload) => api.post("/api/journeys", payload),

  update: async (id, payload) => api.patch(`/api/journeys/${id}`, payload),

  delete: async (id) => api.del(`/api/journeys/${id}`),

  activate: async (id) => api.post(`/api/journeys/${id}/activate`),

  pause: async (id) => api.post(`/api/journeys/${id}/pause`),

  archive: async (id) => api.post(`/api/journeys/${id}/archive`),

  publish: async (id) => api.post(`/api/journeys/${id}/publish`),
};

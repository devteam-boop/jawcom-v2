import { api } from "./apiClient";

export const templateService = {
  list: async (filters = {}) => api.get("/api/templates", filters),
  get: async (id) => api.get(`/api/templates/${id}`),
  create: async (payload) => api.post("/api/templates", payload),
  update: async (id, payload) => api.patch(`/api/templates/${id}`, payload),
  getUsage: async (id) => api.get(`/api/templates/${id}/usage`),
};

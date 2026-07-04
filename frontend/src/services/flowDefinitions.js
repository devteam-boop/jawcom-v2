import { api } from "./apiClient";

export const flowDefinitionService = {
  list: async ({ skip = 0, limit = 100, status } = {}) => {
    const params = { skip, limit };
    if (status) params.status = status;
    return api.get("/api/flow-definitions", params);
  },

  get: async (id) => api.get(`/api/flow-definitions/${id}`),

  create: async (payload) => api.post("/api/flow-definitions", payload),

  update: async (id, payload) => api.patch(`/api/flow-definitions/${id}`, payload),

  delete: async (id) => api.del(`/api/flow-definitions/${id}`),

  publish: async (id) => api.post(`/api/flow-definitions/${id}/publish`),

  archive: async (id) => api.post(`/api/flow-definitions/${id}/archive`),
};

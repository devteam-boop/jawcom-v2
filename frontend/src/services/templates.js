import { api } from "./apiClient";

export const templateService = {
  list: async ({ channel, status } = {}) => {
    const params = {};
    if (channel) params.channel = channel;
    if (status) params.status = status;
    return api.get("/api/templates", params);
  },

  get: async (id) => api.get(`/api/templates/${id}`),

  create: async (payload) => api.post("/api/templates", payload),

  update: async (id, payload) => api.patch(`/api/templates/${id}`, payload),

  delete: async (id) => api.del(`/api/templates/${id}`),

  duplicate: async (id) => api.post(`/api/templates/${id}/duplicate`),

  archive: async (id) => api.post(`/api/templates/${id}/archive`),

  activate: async (id) => api.post(`/api/templates/${id}/activate`),

  getUsage: async (id) => api.get(`/api/templates/${id}/usage`),
};

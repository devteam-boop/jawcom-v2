import { api } from "./apiClient";

export const stageMappingService = {
  list: async ({ skip = 0, limit = 100, journeyId } = {}) => {
    const params = { skip, limit };
    if (journeyId) params.journey_id = journeyId;
    return api.get("/api/stage-mappings", params);
  },

  get: async (id) => api.get(`/api/stage-mappings/${id}`),

  create: async (payload) => api.post("/api/stage-mappings", payload),

  update: async (id, payload) => api.patch(`/api/stage-mappings/${id}`, payload),

  delete: async (id) => api.del(`/api/stage-mappings/${id}`),
};

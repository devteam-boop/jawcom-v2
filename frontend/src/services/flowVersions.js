import { api } from "./apiClient";

export const flowVersionService = {
  list: async ({ skip = 0, limit = 100, flowDefinitionId } = {}) => {
    const params = { skip, limit };
    if (flowDefinitionId) params.flow_definition_id = flowDefinitionId;
    return api.get("/api/flow-versions", params);
  },

  get: async (id) => api.get(`/api/flow-versions/${id}`),

  create: async (payload) => api.post("/api/flow-versions", payload),

  delete: async (id) => api.del(`/api/flow-versions/${id}`),
};

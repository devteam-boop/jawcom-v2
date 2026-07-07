import { api } from "./apiClient";

export const integrationService = {
  list: async () => api.get("/api/integrations"),
  get: async (id) => api.get(`/api/integrations/${id}`),
  connect: async (id, config) => api.post(`/api/integrations/${id}/connect`, config),
  disconnect: async (id) => api.post(`/api/integrations/${id}/disconnect`),
  getHealth: async () => api.get("/api/integrations/health"),
};

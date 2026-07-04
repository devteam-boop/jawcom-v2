import { api } from "./apiClient";

export const inboxService = {
  list: async (filters = {}) => api.get("/api/inbox", filters),
  get: async (id) => api.get(`/api/inbox/${id}`),
  send: async (conversationId, message) =>
    api.post(`/api/inbox/${conversationId}/messages`, message),
  getMessages: async (conversationId) =>
    api.get(`/api/inbox/${conversationId}/messages`),
};

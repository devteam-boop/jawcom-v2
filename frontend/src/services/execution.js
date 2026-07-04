import { api } from "./apiClient";

export const executionService = {
  test: async (payload) => api.post("/api/execution/test", payload),
};

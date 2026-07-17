import { api } from "./apiClient";

export const authService = {
  login: async (password) => api.post("/api/auth/login", { password }),
};

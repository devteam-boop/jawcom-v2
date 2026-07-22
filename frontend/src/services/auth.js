import { api } from "./apiClient";

export const authService = {
  login: ({ email, password, rememberMe }) =>
    api.post("/api/auth/login", { email, password, remember_me: !!rememberMe }),
  logout: () => api.post("/api/auth/logout", {}),
  me: () => api.get("/api/auth/me"),
  forgotPassword: (email) => api.post("/api/auth/forgot-password", { email }),
  resetPassword: ({ email, otp, newPassword }) =>
    api.post("/api/auth/reset-password", { email, otp, new_password: newPassword }),
  updateProfile: ({ fullName }) => api.patch("/api/auth/profile", { full_name: fullName }),
  changePassword: ({ currentPassword, newPassword }) =>
    api.post("/api/auth/change-password", { current_password: currentPassword, new_password: newPassword }),
  listSessions: () => api.get("/api/auth/sessions"),
  revokeSession: (sessionId) => api.post(`/api/auth/sessions/${sessionId}/revoke`, {}),
  loginHistory: (limit = 50) => api.get("/api/auth/login-history", { limit }),
};

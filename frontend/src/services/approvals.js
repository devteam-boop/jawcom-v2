import { api } from "./apiClient";

export const approvalService = {
  list: async (instanceId) => api.get(`/api/approvals/${instanceId}`),

  approve: async (instanceId, approvalId, resolvedBy = "system") =>
    api.post(`/api/approvals/${instanceId}/${approvalId}/approve?resolved_by=${resolvedBy}`),

  reject: async (instanceId, approvalId, resolvedBy = "system") =>
    api.post(`/api/approvals/${instanceId}/${approvalId}/reject?resolved_by=${resolvedBy}`),
};

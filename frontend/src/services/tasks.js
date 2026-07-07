import { api } from "./apiClient";

export const taskService = {
  list: async (instanceId) => api.get(`/api/tasks/${instanceId}`),

  complete: async (instanceId, taskId, completedBy = "system") =>
    api.post(`/api/tasks/${instanceId}/${taskId}/complete?completed_by=${completedBy}`),

  reject: async (instanceId, taskId, completedBy = "system") =>
    api.post(`/api/tasks/${instanceId}/${taskId}/reject?completed_by=${completedBy}`),
};

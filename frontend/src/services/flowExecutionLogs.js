import { api } from "./apiClient";

export const flowExecutionLogService = {
  list: async ({ skip = 0, limit = 100, flowDefinitionId, leadId, runningInstanceId } = {}) => {
    const params = { skip, limit };
    if (flowDefinitionId) params.flow_definition_id = flowDefinitionId;
    if (leadId) params.lead_id = leadId;
    if (runningInstanceId) params.running_instance_id = runningInstanceId;
    return api.get("/api/flow-execution-logs", params);
  },

  get: async (id) => api.get(`/api/flow-execution-logs/${id}`),

  create: async (payload) => api.post("/api/flow-execution-logs", payload),

  delete: async (id) => api.del(`/api/flow-execution-logs/${id}`),
};

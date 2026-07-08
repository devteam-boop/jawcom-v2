import { api } from "./apiClient";

export const communicationEventService = {
  list: async ({ skip = 0, limit = 100, runningInstanceId, journeyId, leadId, eventType } = {}) => {
    const params = { skip, limit };
    if (runningInstanceId) params.running_instance_id = runningInstanceId;
    if (journeyId) params.journey_id = journeyId;
    if (leadId) params.lead_id = leadId;
    if (eventType) params.event_type = eventType;
    return api.get("/api/communication-events", params);
  },

  get: async (id) => api.get(`/api/communication-events/${id}`),
};

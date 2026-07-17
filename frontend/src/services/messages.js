import { api } from "./apiClient";

/**
 * Wraps the existing production send endpoints (backend/app/api/message_routes.py)
 * — no new backend routes. Both accept module="general", context_id=null for a
 * manual (non-journey) send; the resulting communication_events row is
 * indistinguishable in storage from any other send (source="manual" in payload).
 *
 * `token` is the agent session token from useAgentSession() (Phase 3, Task 1)
 * — these routes are Bearer-protected and reject calls with no valid token.
 */
export const messageService = {
  sendEmail: async (payload, token) => api.post("/api/messages/email/send", payload, { token }),
  sendWhatsapp: async (payload, token) => api.post("/api/messages/whatsapp/send", payload, { token }),
};

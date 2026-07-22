import { api } from "./apiClient";

/**
 * Wraps the existing production send endpoints (backend/app/api/message_routes.py)
 * — no new backend routes. Both accept module="general", context_id=null for a
 * manual (non-journey) send; the resulting communication_events row is
 * indistinguishable in storage from any other send (source="manual" in payload).
 *
 * Auth is the logged-in admin's session cookie, sent automatically by the
 * browser (see AuthContext / apiClient's credentials: "include") — no
 * per-send token any more.
 */
export const messageService = {
  sendEmail: async (payload) => api.post("/api/messages/email/send", payload),
  sendWhatsapp: async (payload) => api.post("/api/messages/whatsapp/send", payload),
};

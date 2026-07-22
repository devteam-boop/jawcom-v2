import { resolveEventTimestamp } from "@/lib/dateFormat";

/**
 * WhatsApp 24h customer-service session window — derived entirely from the
 * already-fetched communication_events for a conversation (the same rows
 * useConversations()/ConversationThread already poll every 10s). No new
 * table, no new endpoint: the window is just "has this lead sent a
 * WhatsApp 'replied' event in the last 24h", recomputed on every poll tick
 * so expiry is picked up automatically without a dedicated timer.
 *
 * The anchor is resolveEventTimestamp() of the latest 'replied' event —
 * Meta's own webhook timestamp when available, not this server's insert
 * time (`occurred_at`) — per the "use META's webhook timestamp, NOT
 * created_at" rule: the window must expire 24h after the customer actually
 * replied, not 24h after JawCom happened to record it.
 *
 * Mirrors WHATSAPP_SESSION_WINDOW_HOURS in
 * backend/app/services/communication_event_service.py, which re-checks the
 * same rule server-side before accepting a freeform send.
 */

const SESSION_WINDOW_HOURS = 24;

export function getWhatsappSessionWindow(events = []) {
  const lastInboundAt = events
    .filter((e) => e.channel === "whatsapp" && e.event_type === "replied")
    .reduce((latest, e) => {
      const ts = resolveEventTimestamp(e);
      return ts && (!latest || ts > latest) ? ts : latest;
    }, null);

  if (!lastInboundAt) {
    return { active: false, everReplied: false, lastInboundAt: null, expiresAt: null };
  }

  const expiresAt = new Date(lastInboundAt.getTime() + SESSION_WINDOW_HOURS * 60 * 60 * 1000);
  return {
    active: Date.now() < expiresAt.getTime(),
    everReplied: true,
    lastInboundAt,
    expiresAt,
  };
}

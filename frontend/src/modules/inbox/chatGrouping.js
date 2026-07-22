import { resolveEventTimestamp } from "@/lib/dateFormat";

/**
 * Groups a flat communication_events list into WhatsApp-style chat items —
 * display-layer only, no new data, no change to how events are stored.
 *
 * Every bubble's `anchorTime` (and `readAt`/`deliveredAt`) comes from
 * resolveEventTimestamp() rather than the row's raw `occurred_at` — for a
 * WhatsApp inbound reply or a delivered/read status row, that prefers
 * Meta's own webhook timestamp (already stored in the row's payload, see
 * meta_webhook_routes.py) over this server's insert time, so the bubble
 * timestamp, the conversation's "Last seen" (useConversations.js, same
 * resolver), and the Communication/Journey Timeline all show the identical
 * time for the identical event.
 *
 * - whatsapp_sent/email_sent -> starts an outbound bubble, keyed by
 *   provider_message_id (falls back to event.id when none exists yet).
 * - delivered/read/clicked/failed/bounced/complained -> attach to the
 *   existing bubble with the same provider_message_id as a status upgrade,
 *   never a new bubble. If no matching bubble is found (e.g. a send that
 *   failed before ever getting a provider_message_id, or the anchor fell
 *   outside the fetched event window), it becomes its own standalone
 *   outbound bubble rather than being dropped.
 * - replied -> always its own new inbound bubble (a genuine new message
 *   from the customer), keyed by its own event id so multiple replies to
 *   the same anchor never collapse into one.
 * - everything else (journey_started, trigger_executed, condition_evaluated,
 *   wait_started/completed, note_added, task_created/completed) -> a
 *   centered system separator, not a bubble.
 */

const OUTBOUND_SEND_TYPES = new Set(["whatsapp_sent", "email_sent"]);
const STATUS_UPDATE_TYPES = new Set(["delivered", "read", "clicked", "failed", "bounced", "complained"]);
const NEGATIVE_STATUS_TYPES = new Set(["failed", "bounced", "complained"]);
const STATUS_RANK = { queued: 0, sent: 1, whatsapp_sent: 1, email_sent: 1, delivered: 2, clicked: 2, read: 3 };

export const SYSTEM_EVENT_LABELS = {
  journey_started: "Journey started",
  trigger_executed: "Trigger executed",
  condition_evaluated: "Condition evaluated",
  wait_started: "Waiting",
  wait_completed: "Wait completed",
  note_added: "Note added",
  task_created: "Task created",
  task_completed: "Task completed",
};

// Manual sends (message_routes.py) always populate payload.body/subject.
// Journey-engine sends (ExecutionEngine._record_communication_event) use a
// different shape with no body at all — resolved_template_name + a
// human-readable `message` string instead. Falls back through both so
// "message text is primary" holds regardless of which path produced the
// event; never touches how either path stores data.
function outboundText(eventType, payload) {
  const subject = eventType === "email_sent" ? payload.subject || null : null;
  const text =
    payload.body ||
    (payload.resolved_template_name ? `Template: ${payload.resolved_template_name}` : null) ||
    payload.message ||
    "";
  return { subject, text };
}

function eventTimeMs(e) {
  return resolveEventTimestamp(e)?.getTime() ?? 0;
}

export function groupIntoChatItems(events = []) {
  const sorted = [...events].sort((a, b) => eventTimeMs(a) - eventTimeMs(b));
  const bubblesByKey = new Map();
  const items = [];

  for (const e of sorted) {
    const payload = e.payload || {};

    if (OUTBOUND_SEND_TYPES.has(e.event_type)) {
      const key = e.provider_message_id || e.id;
      const { subject, text } = outboundText(e.event_type, payload);
      const bubble = {
        type: "bubble",
        direction: "out",
        key,
        anchorTime: resolveEventTimestamp(e),
        subject,
        text,
        channel: e.channel,
        provider: e.provider,
        source: payload.source,
        status: e.event_type,
        errorReason: null,
        readAt: null,
        deliveredAt: null,
        raw: [e],
      };
      bubblesByKey.set(key, bubble);
      items.push(bubble);
      continue;
    }

    if (e.event_type === "replied") {
      items.push({
        type: "bubble",
        direction: "in",
        key: e.id,
        anchorTime: resolveEventTimestamp(e),
        subject: null,
        text: payload.body || "(no message text)",
        channel: e.channel,
        provider: e.provider,
        source: null,
        status: null,
        errorReason: null,
        raw: [e],
      });
      continue;
    }

    if (STATUS_UPDATE_TYPES.has(e.event_type)) {
      const bubble = e.provider_message_id ? bubblesByKey.get(e.provider_message_id) : null;
      if (bubble) {
        if (NEGATIVE_STATUS_TYPES.has(e.event_type)) {
          bubble.status = e.event_type;
          bubble.errorReason = payload.error || null;
        } else if ((STATUS_RANK[e.event_type] ?? 0) >= (STATUS_RANK[bubble.status] ?? 0)) {
          bubble.status = e.event_type;
          if (e.event_type === "read") bubble.readAt = resolveEventTimestamp(e);
          if (e.event_type === "delivered") bubble.deliveredAt = resolveEventTimestamp(e);
        }
        bubble.raw.push(e);
        continue;
      }
      // Unmatched — most commonly an outbound send that failed before a
      // provider_message_id ever existed. Stands alone rather than being lost.
      items.push({
        type: "bubble",
        direction: "out",
        key: e.id,
        anchorTime: resolveEventTimestamp(e),
        subject: payload.subject || null,
        text: payload.body || "(message unavailable)",
        channel: e.channel,
        provider: e.provider,
        source: payload.source,
        status: e.event_type,
        errorReason: payload.error || null,
        readAt: null,
        deliveredAt: null,
        raw: [e],
      });
      continue;
    }

    items.push({
      type: "system",
      key: e.id,
      anchorTime: resolveEventTimestamp(e),
      eventType: e.event_type,
      label: SYSTEM_EVENT_LABELS[e.event_type] || e.event_type.replace(/_/g, " "),
      detail: payload.resolved_note || payload.note || payload.title || null,
      raw: [e],
    });
  }

  items.sort((a, b) => (a.anchorTime?.getTime() ?? 0) - (b.anchorTime?.getTime() ?? 0));
  return items;
}

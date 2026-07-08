/**
 * One-line preview text for a communication event, used only by the Inbox
 * conversation list row. Deliberately separate from CommunicationTimeline's
 * own per-event label map (that map renders the full timeline entry —
 * icon/status/channel/provider/expandable payload; this just needs a short
 * string for a list row) so CommunicationTimeline itself is never
 * duplicated or modified.
 */
export function previewFor(event) {
  if (!event) return "No activity yet";
  const payload = event.payload || {};

  switch (event.event_type) {
    case "journey_started":
      return `Journey started${payload.journey_name ? `: ${payload.journey_name}` : ""}`;
    case "trigger_executed":
      return "Trigger executed";
    case "condition_evaluated":
      return `Condition evaluated${"condition_result" in payload ? ` (${payload.condition_result})` : ""}`;
    case "wait_started":
      return `Waiting ${payload.duration ?? ""} ${payload.unit ?? ""}`.trim();
    case "wait_completed":
      return "Wait completed";
    case "whatsapp_sent":
      return `WhatsApp sent: ${payload.resolved_template_name || payload.template_id || "message"}`;
    case "email_sent":
      return `Email sent: ${payload.resolved_template_name || payload.template_id || "message"}`;
    case "note_added":
      return payload.resolved_note || payload.note || "Note added";
    case "task_created":
      return `Task created: ${payload.title || ""}`.trim();
    case "task_completed":
      return `Task completed: ${payload.title || ""}`.trim();
    default:
      return event.event_type
        ? event.event_type.replace(/_/g, " ")
        : "Activity recorded";
  }
}

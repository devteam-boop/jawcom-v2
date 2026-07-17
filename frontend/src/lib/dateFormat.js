import { format, formatDistanceToNow, isToday, isYesterday } from "date-fns";

/**
 * Single shared source of timestamp formatting for the whole app. Renders
 * in the browser's local timezone (IST for this deployment) — never raw
 * ISO strings or UTC. Every component that shows a timestamp should go
 * through one of these instead of calling `new Date(...).toLocaleString()`
 * or printing the raw string directly.
 */

function toDate(value) {
  if (!value) return null;
  const d = value instanceof Date ? value : new Date(value);
  return Number.isNaN(d.getTime()) ? null : d;
}

/** "17 Jul 2026, 09:45 AM" */
export function formatDateTime(value) {
  const d = toDate(value);
  return d ? format(d, "dd MMM yyyy, hh:mm a") : "—";
}

/** "17 Jul 2026" */
export function formatDate(value) {
  const d = toDate(value);
  return d ? format(d, "dd MMM yyyy") : "—";
}

/** "09:45 AM" */
export function formatTime(value) {
  const d = toDate(value);
  return d ? format(d, "hh:mm a") : "—";
}

/** "2 mins ago" / "Yesterday" / "3 hours ago" */
export function formatRelative(value) {
  const d = toDate(value);
  if (!d) return "—";
  if (isToday(d)) return formatDistanceToNow(d, { addSuffix: true });
  if (isYesterday(d)) return "Yesterday";
  return formatDistanceToNow(d, { addSuffix: true });
}

/** "17 Jul 2026, 09:45 AM · 2 mins ago" — the default combined display. */
export function formatDateTimeWithRelative(value) {
  const d = toDate(value);
  if (!d) return "—";
  return `${formatDateTime(d)} · ${formatRelative(d)}`;
}

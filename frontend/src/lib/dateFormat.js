import { formatDistanceToNow } from "date-fns";

/**
 * Single shared source of timestamp formatting for the whole app — Dashboard,
 * Inbox, Campaigns, Journeys/Journey Monitor, Contacts, Templates,
 * Communication Timeline, Notifications all import from here. Every
 * component that shows a timestamp goes through one of these instead of
 * calling `new Date(...).toLocaleString()`, printing a raw string, or
 * reaching for a second date util.
 *
 * TIMEZONE CONTRACT (fixes "same event shows different times in different
 * places"): the backend always stores and serializes naive UTC wall-clock
 * datetimes (`datetime.utcnow()` + Pydantic `v.isoformat()`, no offset/Z
 * ever included — see backend/app/communication_events/schemas.py and
 * friends). Every render here:
 *   1. Treats any timestamp string with no timezone designator as UTC
 *      (toDate() below) — never as "whatever zone this browser/OS happens
 *      to be in", which is what `new Date(naiveString)` does natively and
 *      is the root cause of the inconsistency bug.
 *   2. Always renders in a FIXED Asia/Kolkata (IST) zone via
 *      Intl.DateTimeFormat({ timeZone: "Asia/Kolkata" }) — never the
 *      browser's local zone, and never date-fns' `format()` (which reads
 *      local Date getters and is local-zone-dependent).
 * The result: the same stored instant renders identically everywhere,
 * regardless of which machine/browser/OS timezone is doing the rendering.
 */

const IST_TIME_ZONE = "Asia/Kolkata";

function toDate(value) {
  if (!value) return null;
  if (value instanceof Date) return Number.isNaN(value.getTime()) ? null : value;
  let s = String(value);
  // A naive "T"-datetime string with no trailing Z/offset is a backend
  // timestamp that IS UTC but doesn't say so — make that explicit so
  // `new Date(...)` parses it as a UTC instant instead of local time (its
  // native behavior for zone-less datetime strings, which is what caused
  // the same event to render differently depending on the browser's own
  // timezone). Bare date-only strings ("2026-07-25", no time part) are
  // already spec'd to parse as UTC and are left untouched. Already-zoned
  // strings (trailing Z or +HH:MM/-HH:MM, e.g. a third-party webhook's own
  // timestamp) are left untouched too.
  if (/T\d{2}:\d{2}/.test(s) && !/[zZ]$|[+-]\d{2}:?\d{2}$/.test(s)) {
    s = `${s}Z`;
  }
  const d = new Date(s);
  return Number.isNaN(d.getTime()) ? null : d;
}

function istFormatter(options) {
  return new Intl.DateTimeFormat("en-GB", { timeZone: IST_TIME_ZONE, ...options });
}

// "22 Jul 2026"
function istDatePart(d) {
  return istFormatter({ day: "2-digit", month: "short", year: "numeric" }).format(d);
}

// "09:15 AM" — en-US specifically: en-GB renders lowercase "am/pm".
function istTimePart(d, withSeconds = false) {
  return new Intl.DateTimeFormat("en-US", {
    timeZone: IST_TIME_ZONE,
    hour: "2-digit",
    minute: "2-digit",
    second: withSeconds ? "2-digit" : undefined,
    hour12: true,
  }).format(d);
}

// "08:41:12" — 24h, for the tooltip's unambiguous full-precision form.
function istTime24Seconds(d) {
  return new Intl.DateTimeFormat("en-GB", {
    timeZone: IST_TIME_ZONE,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).format(d);
}

// "2026-07-22" in IST — used for day-boundary comparisons (Today/Yesterday
// detection, Inbox day dividers) so they're computed against IST midnight,
// never the browser's own local midnight.
export function getISTDateKey(value) {
  const d = toDate(value);
  if (!d) return null;
  const parts = istFormatter({ year: "numeric", month: "2-digit", day: "2-digit" }).formatToParts(d);
  const map = Object.fromEntries(parts.map((p) => [p.type, p.value]));
  return `${map.year}-${map.month}-${map.day}`;
}

function isSameISTDay(a, b) {
  const ka = getISTDateKey(a);
  const kb = getISTDateKey(b);
  return !!ka && ka === kb;
}

/** "22 Jul 2026, 09:15 AM" */
export function formatDateTime(value) {
  const d = toDate(value);
  return d ? `${istDatePart(d)}, ${istTimePart(d)}` : "—";
}

/** "22 Jul 2026" */
export function formatDate(value) {
  const d = toDate(value);
  return d ? istDatePart(d) : "—";
}

/** "09:15 AM" */
export function formatTime(value) {
  const d = toDate(value);
  return d ? istTimePart(d) : "—";
}

/** "22 Jul 2026, 08:40:12 AM" — Audits + Journey/Communication Timeline,
 * where the exact sequence of same-minute events matters. */
export function formatDateTimeSeconds(value) {
  const d = toDate(value);
  return d ? `${istDatePart(d)}, ${istTimePart(d, true)}` : "—";
}

/** "2 mins ago" / "Yesterday" / "3 hours ago" — duration-based, so it's
 * timezone-agnostic by nature; only the Today/Yesterday day-boundary check
 * is anchored to IST rather than the browser's local day. Secondary/tooltip
 * use only — never the primary display (see formatDateTimeWithRelative). */
export function formatRelative(value) {
  const d = toDate(value);
  if (!d) return "—";
  const now = new Date();
  if (isSameISTDay(d, now)) return formatDistanceToNow(d, { addSuffix: true });
  const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);
  if (isSameISTDay(d, yesterday)) return "Yesterday";
  return formatDistanceToNow(d, { addSuffix: true });
}

/**
 * "Today, 11:42 AM" / "Yesterday, 04:17 PM" / "22 Jul 2026, 09:15 AM" — the
 * default primary display used across the app (Dashboard, Inbox, Contacts,
 * Journeys, Templates, Communication Timeline, Notifications). Exact time,
 * always IST, with a relative-day shorthand only for today/yesterday —
 * never a bare "about 8 hours ago" as the primary label.
 */
export function formatDateTimeWithRelative(value) {
  const d = toDate(value);
  if (!d) return "—";
  const now = new Date();
  if (isSameISTDay(d, now)) return `Today, ${istTimePart(d)}`;
  const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);
  if (isSameISTDay(d, yesterday)) return `Yesterday, ${istTimePart(d)}`;
  return formatDateTime(d);
}

/** "22 Jul 2026 08:41:12 IST" — full-precision hover-tooltip form (Journey
 * Monitor "Last Activity" and anywhere else exact-to-the-second confirmation
 * is useful next to a shorthand/relative primary label). */
export function formatTooltip(value) {
  const d = toDate(value);
  return d ? `${istDatePart(d)} ${istTime24Seconds(d)} IST` : "—";
}

/**
 * Resolves the single "true" timestamp for a communication_events row —
 * the source-of-truth entry point for RULE 1 ("every UI timestamp must come
 * from that event's OWN stored timestamp"). For provider-sourced rows
 * (WhatsApp inbound messages/status webhooks), Meta's own webhook
 * `timestamp` (epoch seconds, nested in the row's stored raw payload —
 * meta_webhook_routes.py already persists `raw_message`/`raw_status`
 * verbatim, no schema change needed) is preferred over `occurred_at` (this
 * server's insert time for that row), per RULE 2 ("Customer replies: use
 * META's webhook timestamp, NOT created_at, when Meta provides one" — same
 * reasoning applies to delivered/read/failed status rows). Every surface
 * that renders a communication_events row (Inbox, Dashboard activity,
 * Communication Timeline, Journey Activity) must call this before
 * formatting, or the same event can show two different times on two
 * screens depending on which field each screen happened to read.
 *
 * Falls back to `occurred_at` for every other event (journey/system events,
 * manual sends, or a provider row with no nested timestamp) — that IS the
 * event's own stored timestamp already; no new column needed.
 */
export function resolveEventTimestamp(event) {
  if (!event) return null;
  const payload = event.payload || {};
  const providerTimestamp = payload.raw_message?.timestamp ?? payload.raw_status?.timestamp;
  if (providerTimestamp != null) {
    const ms = Number(providerTimestamp) * 1000;
    if (Number.isFinite(ms)) return new Date(ms);
  }
  return toDate(event.occurred_at);
}

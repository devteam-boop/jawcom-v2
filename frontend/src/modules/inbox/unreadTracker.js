/**
 * Placeholder unread tracking.
 *
 * The backend has no read/unread state at all — CommunicationEvent has no
 * such column, and there is no per-user session/auth system to attach one
 * to (see docs: "No authentication"). Building that is backend/auth work,
 * explicitly out of scope here ("Do not redesign backend unless absolutely
 * required").
 *
 * This is a client-only, browser-local placeholder: it remembers when a
 * conversation was last opened *in this browser* and treats any activity
 * newer than that as unread. It is not a real multi-user read receipt
 * system — just enough to make the unread indicator meaningful for local
 * testing/demo, clearly separable from real backend-backed state later.
 */
const STORAGE_KEY = "jawcom.inbox.lastSeen";

function readStore() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {};
  } catch {
    return {};
  }
}

function writeStore(store) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(store));
  } catch {
    // localStorage unavailable (SSR/private mode) — unread indicator simply
    // won't persist across reloads; not fatal.
  }
}

export function markConversationSeen(leadId) {
  const store = readStore();
  store[leadId] = new Date().toISOString();
  writeStore(store);
}

export function isConversationUnread(leadId, lastActivityAt) {
  if (!lastActivityAt) return false;
  const store = readStore();
  const lastSeen = store[leadId];
  if (!lastSeen) return true;
  return new Date(lastActivityAt) > new Date(lastSeen);
}

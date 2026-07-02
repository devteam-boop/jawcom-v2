const BASE = "/api/inbox";

export const inboxService = {
  list: async (filters = {}) => {
    const params = new URLSearchParams(filters);
    const res = await fetch(`${BASE}?${params}`);
    if (!res.ok) throw new Error("Failed to list conversations");
    return res.json();
  },
  get: async (id) => {
    const res = await fetch(`${BASE}/${id}`);
    if (!res.ok) throw new Error("Failed to get conversation");
    return res.json();
  },
  send: async (conversationId, message) => {
    const res = await fetch(`${BASE}/${conversationId}/messages`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(message),
    });
    if (!res.ok) throw new Error("Failed to send message");
    return res.json();
  },
  getMessages: async (conversationId) => {
    const res = await fetch(`${BASE}/${conversationId}/messages`);
    if (!res.ok) throw new Error("Failed to get messages");
    return res.json();
  },
};

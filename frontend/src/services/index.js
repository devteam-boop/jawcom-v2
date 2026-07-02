<<<<<<< HEAD
export { inboxService } from "./inbox";
export { journeyService } from "./journeys";
export { campaignService } from "./campaigns";
export { templateService } from "./templates";
export { reportService } from "./reports";
export { integrationService } from "./integrations";
export { jawisService } from "./jawis";
=======
// Empty typed placeholder services. Wire these to a real backend later.
// All functions return promises with hardcoded dummy data so the call sites
// can be swapped to fetch/axios without changing signatures.

export const conversationService = {
  list: async () => [],
  get: async (_id) => null,
  send: async (_id, _message) => ({ ok: true }),
};

export const customerService = {
  list: async () => [],
  get: async (_id) => null,
  update: async (_id, _patch) => ({ ok: true }),
};

export const campaignService = {
  list: async () => [],
  create: async (_payload) => ({ ok: true }),
};

export const journeyService = {
  list: async () => [],
  toggle: async (_id) => ({ ok: true }),
};

export const followupService = {
  list: async (_bucket) => [],
  complete: async (_id) => ({ ok: true }),
};

export const reportsService = {
  summary: async () => ({}),
};

export const integrationsService = {
  list: async () => [],
  connect: async (_id) => ({ ok: true }),
};

export const assistantService = {
  suggestions: async () => [],
  ask: async (_prompt) => ({ ok: true, text: "" }),
};
>>>>>>> 321075ad65aa3df54916ae638505753705e9661b

import { api } from "./apiClient";

// Client for /api/whatsapp-templates — the Meta-synced WhatsApp template
// lifecycle (Draft -> Submit to Meta -> webhook/sync approval). Distinct
// from services/templates.js (the generic email/sms/whatsapp/push CRUD
// table): that service's create/update never write to whatsapp_templates,
// so the WhatsApp admin lifecycle screen talks to this dedicated client
// instead.
export const whatsappTemplateService = {
  list: async ({ status, language, search } = {}) => {
    const params = {};
    if (status) params.status = status;
    if (language) params.language = language;
    if (search) params.search = search;
    return api.get("/api/whatsapp-templates", params);
  },

  createDraft: async (payload) => api.post("/api/whatsapp-templates", payload),

  submit: async (id) => api.post(`/api/whatsapp-templates/${id}/submit`),

  getVersions: async (id) => api.get(`/api/whatsapp-templates/${id}/versions`),

  preview: async (id, variables = {}) =>
    api.post(`/api/whatsapp-templates/${id}/preview`, { variables }),

  sync: async () => api.post("/api/whatsapp-templates/sync"),

  syncStatus: async () => api.get("/api/whatsapp-templates/sync-status"),
};

import { api } from "./apiClient";

// Wraps the one new endpoint added in Phase 3 (Task 5) — generic draft-text
// transforms for the composer. Reuses AI Lead Assistant's/AI Summary's
// existing Anthropic client/config, not a new integration.
export const aiTextService = {
  transform: async (text, action, targetLanguage) =>
    api.post("/api/ai/transform", { text, action, target_language: targetLanguage }),
};

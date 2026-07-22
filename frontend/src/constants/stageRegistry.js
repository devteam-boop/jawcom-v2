/**
 * Centralized Journey Trigger stage registry — the single source of truth
 * for every stage dropdown (Trigger Builder, Journey list labels, etc.).
 * Do not hardcode a stage list in any component — import STAGES (or the
 * existing frontend/src/services/stageProvider.js#getLeadStages(), which
 * now reads from here) instead.
 *
 * `value` is the internal key persisted as stage_mappings.stage_key and
 * consumed as-is by the Journey Engine at execution time (see
 * backend/app/models/stage_mapping.py — a free-form string column, no
 * backend enum). NEVER rename or remove an existing `value` — existing
 * stage_mappings rows and published journeys key off it directly, and
 * doing so would silently break them. `label` is presentation-only and
 * safe to change at any time without touching stored data.
 *
 * Order here is the literal dropdown order — matches the current
 * NextMoveIn/JAWIS pipeline: New -> Follow-Up -> Qualified -> Options
 * Shared -> Site Visit Scheduled -> Site Visit Completed -> Negotiation
 * -> Won -> Lost.
 */
export const STAGES = [
  { value: "new", label: "New" },
  // Internal key stays "contacted" for backward compatibility — only the
  // display label changed (was "Contacted").
  { value: "contacted", label: "Follow-Up" },
  { value: "qualified", label: "Qualified" },
  // NextMoveIn demand stages — additive, no existing journey/
  // stage_mapping references these keys yet, so nothing executes for them
  // until a journey is actually wired to one.
  { value: "options_shared", label: "Options Shared" },
  { value: "site_visit_scheduled", label: "Site Visit Scheduled" },
  { value: "site_visit_completed", label: "Site Visit Completed" },
  { value: "negotiation", label: "Negotiation" },
  { value: "won", label: "Won" },
  { value: "lost", label: "Lost" },
];

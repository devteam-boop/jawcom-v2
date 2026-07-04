/**
 * StageProvider — abstracts lead stage resolution.
 *
 * JAWIS is the source of truth for lead stages.
 * JAWCOM must NEVER maintain its own stage master.
 *
 * Today:  Returns temporary stages from a local provider.
 * Future: Replace implementation with JAWIS API call.
 */

const LOCAL_STAGES = [
  { value: "new", label: "New" },
  { value: "contacted", label: "Contacted" },
  { value: "qualified", label: "Qualified" },
  { value: "proposal_shared", label: "Proposal Shared" },
  { value: "negotiation", label: "Negotiation" },
  { value: "won", label: "Won" },
  { value: "lost", label: "Lost" },
];

/**
 * Return available lead stages.
 *
 * @returns {Promise<Array<{value: string, label: string}>>}
 */
export async function getLeadStages() {
  return LOCAL_STAGES;
}

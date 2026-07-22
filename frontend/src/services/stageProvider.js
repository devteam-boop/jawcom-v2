/**
 * StageProvider — abstracts lead stage resolution.
 *
 * JAWIS is the source of truth for lead stages.
 * JAWCOM must NEVER maintain its own stage master.
 *
 * Today:  Returns the stage list from the centralized registry
 *         (frontend/src/constants/stageRegistry.js).
 * Future: Replace implementation with JAWIS API call.
 */

import { STAGES } from "@/constants/stageRegistry";

/**
 * Return available lead stages.
 *
 * @returns {Promise<Array<{value: string, label: string}>>}
 */
export async function getLeadStages() {
  return STAGES;
}

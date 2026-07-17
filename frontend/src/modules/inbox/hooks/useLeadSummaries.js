import { useState, useEffect, useRef } from "react";
import { jawisService } from "@/services/jawis";

/**
 * Fetches + caches GET /api/leads/{id}/summary (name/phone/email/stage) for
 * a set of lead ids, keyed by leadId. Only fetches ids it hasn't already
 * resolved (success or failure) — safe to call again on every poll tick
 * with the same/growing id list without re-hitting JAWIS for ids already
 * known.
 *
 * On any failure (JAWIS unreachable, lead not found) the entry is cached as
 * `null` rather than retried forever — callers fall back to "Lead #<id>",
 * matching the existing convention in LeadDetailsCard.jsx.
 */
export function useLeadSummaries(leadIds = []) {
  const [summaries, setSummaries] = useState({});
  const fetchedRef = useRef(new Set());

  useEffect(() => {
    const toFetch = leadIds.filter((id) => id != null && !fetchedRef.current.has(id));
    if (toFetch.length === 0) return;
    toFetch.forEach((id) => fetchedRef.current.add(id));

    Promise.allSettled(toFetch.map((id) => jawisService.getLead(id))).then((results) => {
      setSummaries((prev) => {
        const next = { ...prev };
        results.forEach((result, i) => {
          next[toFetch[i]] = result.status === "fulfilled" ? result.value : null;
        });
        return next;
      });
    });
  }, [leadIds]);

  return summaries;
}

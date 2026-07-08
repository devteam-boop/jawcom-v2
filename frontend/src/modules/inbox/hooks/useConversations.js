import { useState, useEffect, useCallback } from "react";
import { communicationEventService } from "@/services/communicationEvents";

/**
 * One conversation per lead, derived entirely from the existing
 * communication-events API (GET /api/communication-events) — no new
 * backend endpoint.
 *
 * The API has no "group by lead, latest first" aggregate query, so this
 * fetches the max page size (500) and groups client-side. Reasonable at
 * current data volume; at real scale this would need a backend aggregate
 * endpoint — deliberately not built here per "Do not redesign backend
 * unless absolutely required".
 */
export function useConversations() {
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetch = useCallback(async () => {
    try {
      setLoading(true);
      const events = await communicationEventService.list({ limit: 500 });

      const byLead = new Map();
      events.forEach((event) => {
        const leadId = event.lead_id;
        if (!byLead.has(leadId)) byLead.set(leadId, []);
        byLead.get(leadId).push(event);
      });

      const grouped = Array.from(byLead.entries()).map(([leadId, leadEvents]) => {
        const sorted = [...leadEvents].sort(
          (a, b) => new Date(a.occurred_at) - new Date(b.occurred_at)
        );
        const latestEvent = sorted[sorted.length - 1];
        const channels = Array.from(
          new Set(sorted.map((e) => e.channel).filter((c) => c && c !== "system"))
        );
        return {
          leadId,
          events: sorted,
          latestEvent,
          lastActivityAt: latestEvent?.occurred_at || null,
          channels,
        };
      });

      grouped.sort((a, b) => new Date(b.lastActivityAt) - new Date(a.lastActivityAt));

      setConversations(grouped);
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetch(); }, [fetch]);

  useEffect(() => {
    const interval = setInterval(fetch, 10000);
    return () => clearInterval(interval);
  }, [fetch]);

  return { conversations, loading, error, refetch: fetch };
}

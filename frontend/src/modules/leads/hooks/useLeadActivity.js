import { useState, useEffect, useCallback } from "react";
import { runningInstanceService } from "@/services/runningInstances";
import { communicationEventService } from "@/services/communicationEvents";
import { taskService } from "@/services/tasks";

/**
 * Aggregates everything the Lead Activity page needs for a single lead,
 * across all of that lead's running journey instances. Reuses existing,
 * unmodified APIs only:
 *   - GET /api/running-instances?lead_id=       (Running Journeys / Journey Status)
 *   - GET /api/communication-events?lead_id=    (Activity Timeline / Notes)
 *   - GET /api/tasks/{instance_id}               (Tasks — fanned out per instance,
 *     since there is no lead-scoped tasks endpoint; tasks live in each
 *     instance's data JSON, not a separate table)
 *
 * No new backend endpoints. No changes to the event model or engine.
 */
export function useLeadActivity(leadId) {
  const [instances, setInstances] = useState([]);
  const [events, setEvents] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetch = useCallback(async () => {
    if (!leadId) return;
    try {
      setLoading(true);
      const [instanceData, eventData] = await Promise.all([
        runningInstanceService.list({ leadId, limit: 200 }),
        communicationEventService.list({ leadId, limit: 500 }),
      ]);
      setInstances(instanceData);
      setEvents(eventData);

      const perInstanceTasks = await Promise.all(
        instanceData.map((inst) =>
          taskService
            .list(inst.id)
            .then((list) => list.map((t) => ({ ...t, instance_id: inst.id, journey_id: inst.journey_id })))
            .catch(() => [])
        )
      );
      setTasks(perInstanceTasks.flat());
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, [leadId]);

  useEffect(() => { fetch(); }, [fetch]);

  useEffect(() => {
    if (!leadId) return undefined;
    const interval = setInterval(fetch, 10000);
    return () => clearInterval(interval);
  }, [leadId, fetch]);

  return { instances, events, tasks, loading, error, refetch: fetch };
}

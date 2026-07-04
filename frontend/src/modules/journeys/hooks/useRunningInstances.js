import { useState, useEffect, useCallback } from "react";
import { runningInstanceService } from "@/services/runningInstances";

export function useRunningInstances(journeyId) {
  const [instances, setInstances] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetch = useCallback(async () => {
    try {
      setLoading(true);
      const data = await runningInstanceService.list({ journeyId });
      setInstances(data);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, [journeyId]);

  useEffect(() => { fetch(); }, [fetch]);

  return { instances, loading, error, refetch: fetch };
}

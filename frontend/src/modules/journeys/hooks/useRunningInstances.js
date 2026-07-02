import { useState, useEffect } from "react";
import { journeyService } from "@/services";

export function useRunningInstances(journeyId) {
  const [instances, setInstances] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetch = async () => {
    if (!journeyId) return;
    try {
      setLoading(true);
      const data = await journeyService.getRunningInstances(journeyId);
      setInstances(data);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetch(); }, [journeyId]);

  return { instances, loading, error, refetch: fetch };
}

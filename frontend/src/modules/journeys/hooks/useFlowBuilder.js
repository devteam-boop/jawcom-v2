import { useState, useEffect, useCallback } from "react";
import { journeyService } from "@/services";

export function useFlowBuilder(journeyId) {
  const [flow, setFlow] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const fetch = useCallback(async () => {
    if (!journeyId) return;
    try {
      setLoading(true);
      const data = await journeyService.getFlow(journeyId);
      setFlow(data);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, [journeyId]);

  useEffect(() => { fetch(); }, [fetch]);

  const save = async (flowDefinition) => {
    try {
      setSaving(true);
      const updated = await journeyService.saveFlow(journeyId, flowDefinition);
      setFlow(updated);
    } catch (err) {
      setError(err);
    } finally {
      setSaving(false);
    }
  };

  return { flow, loading, saving, error, save, refetch: fetch };
}

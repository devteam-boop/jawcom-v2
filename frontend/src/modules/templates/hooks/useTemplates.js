import { useState, useEffect, useCallback } from "react";
import { templateService } from "@/services/templates";

export function useTemplates(channel) {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetch = useCallback(async () => {
    try {
      setLoading(true);
      const data = await templateService.list(channel ? { channel } : {});
      setTemplates(data);
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, [channel]);

  useEffect(() => { fetch(); }, [fetch]);

  return { templates, loading, error, refetch: fetch };
}

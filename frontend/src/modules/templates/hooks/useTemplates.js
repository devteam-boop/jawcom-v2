import { useState, useEffect } from "react";
import { templateService } from "@/services";

export function useTemplates(channel) {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetch = async () => {
    try {
      setLoading(true);
      const filters = channel ? { channel } : {};
      const data = await templateService.list(filters);
      setTemplates(data);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetch(); }, [channel]);

  return { templates, loading, error, refetch: fetch };
}

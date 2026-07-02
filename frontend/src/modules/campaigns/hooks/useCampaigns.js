import { useState, useEffect } from "react";
import { campaignService } from "@/services";

export function useCampaigns() {
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetch = async () => {
    try {
      setLoading(true);
      const data = await campaignService.list();
      setCampaigns(data);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetch(); }, []);

  return { campaigns, loading, error, refetch: fetch };
}

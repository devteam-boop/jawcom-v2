import { useState, useEffect } from "react";
import { journeyService } from "@/services";

export function useJourneys() {
  const [journeys, setJourneys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetch = async () => {
    try {
      setLoading(true);
      const data = await journeyService.list();
      setJourneys(data);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetch(); }, []);

  return { journeys, loading, error, refetch: fetch };
}

export function useJourney(id) {
  const [journey, setJourney] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetch = async () => {
    if (!id) return;
    try {
      setLoading(true);
      const data = await journeyService.get(id);
      setJourney(data);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetch(); }, [id]);

  return { journey, loading, error, refetch: fetch };
}

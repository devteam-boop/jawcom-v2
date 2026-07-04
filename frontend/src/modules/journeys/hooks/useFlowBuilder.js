import { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";
import { flowDefinitionService } from "@/services/flowDefinitions";
import { journeyService } from "@/services/journeys";

export function useFlowBuilder(journeyId) {
  const [flow, setFlow] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [error, setError] = useState(null);

  const fetch = useCallback(async () => {
    if (!journeyId) return;
    try {
      setLoading(true);
      setError(null);
      const journey = await journeyService.get(journeyId);
      if (journey.flow_definition_id) {
        const def = await flowDefinitionService.get(journey.flow_definition_id);
        setFlow(def);
      } else {
        setFlow(null);
      }
    } catch (err) {
      const msg = err?.message || "Failed to load flow";
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }, [journeyId]);

  useEffect(() => {
    fetch();
  }, [fetch]);

  const save = useCallback(
    async (flowDefinition) => {
      try {
        setSaving(true);
        setError(null);
        const journey = await journeyService.get(journeyId);
        if (journey.flow_definition_id && flow?.id) {
          const updated = await flowDefinitionService.update(flow.id, {
            definition: flowDefinition,
          });
          setFlow(updated);
        } else {
          const created = await flowDefinitionService.create({
            name: `Flow for ${journey.name || journeyId}`,
            definition: flowDefinition,
          });
          await journeyService.update(journeyId, {
            flow_definition_id: created.id,
          });
          setFlow(created);
        }
        toast.success("Flow saved successfully");
      } catch (err) {
        const msg = err?.message || "Failed to save flow";
        setError(msg);
        toast.error(msg);
      } finally {
        setSaving(false);
      }
    },
    [journeyId, flow]
  );

  const publish = useCallback(
    async (flowId) => {
      try {
        setPublishing(true);
        setError(null);
        await flowDefinitionService.publish(flowId);
        const updated = await flowDefinitionService.get(flowId);
        setFlow(updated);
        toast.success("Flow published successfully");
      } catch (err) {
        const msg = err?.message || "Failed to publish flow";
        setError(msg);
        toast.error(msg);
      } finally {
        setPublishing(false);
      }
    },
    []
  );

  return { flow, loading, saving, publishing, error, save, publish, refetch: fetch };
}

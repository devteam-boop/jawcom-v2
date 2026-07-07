import { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";
import { flowDefinitionService } from "@/services/flowDefinitions";
import { journeyService } from "@/services/journeys";

export function useFlowBuilder(journeyId) {
  const [flow, setFlow] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [validating, setValidating] = useState(false);
  const [validation, setValidation] = useState(null);
  const [error, setError] = useState(null);

  const fetch = useCallback(async () => {
    if (!journeyId) return;
    try {
      setLoading(true);
      setError(null);
      setValidation(null);
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

  const validate = useCallback(
    async (flowId) => {
      if (!flowId) {
        toast.error("Save the flow first before validating");
        return null;
      }
      try {
        setValidating(true);
        setError(null);
        const result = await flowDefinitionService.validate(flowId);
        setValidation(result);
        if (result.valid) {
          toast.success("Flow validation passed");
        } else {
          const count = result.errors?.length || 0;
          toast.error(`Validation failed — ${count} error${count !== 1 ? "s" : ""} found`);
        }
        return result;
      } catch (err) {
        const msg = err?.message || "Failed to validate flow";
        setError(msg);
        toast.error(msg);
        return null;
      } finally {
        setValidating(false);
      }
    },
    []
  );

  const publish = useCallback(
    async (flowId) => {
      try {
        setPublishing(true);
        setError(null);
        setValidation(null);
        await flowDefinitionService.publish(flowId);
        const updated = await flowDefinitionService.get(flowId);
        setFlow(updated);
        toast.success("Flow published successfully");
      } catch (err) {
        const msg = err?.message || "Failed to publish flow";
        if (err?.body?.detail?.errors) {
          const detail = err.body.detail;
          setValidation(detail);
          const count = detail.errors?.length || 0;
          toast.error(`Publish blocked — ${count} validation error${count !== 1 ? "s" : ""} remaining`);
        } else {
          setError(msg);
          toast.error(msg);
        }
      } finally {
        setPublishing(false);
      }
    },
    []
  );

  return {
    flow, loading, saving, publishing, validating, validation,
    error, save, validate, publish, refetch: fetch,
  };
}

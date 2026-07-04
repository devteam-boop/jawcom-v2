import { useState, useEffect } from "react";
import { toast } from "sonner";
import { stageMappingService } from "@/services/stageMappings";
import { getLeadStages } from "@/services/stageProvider";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Loader2, Target } from "lucide-react";

export default function TriggerConfiguration({ journeyId, mappings = [], onRefresh }) {
  const triggerMapping = mappings.length > 0 ? mappings[0] : null;
  const [stages, setStages] = useState([]);
  const [selectedStage, setSelectedStage] = useState(triggerMapping?.stage_key || "");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getLeadStages().then(setStages);
  }, []);

  const handleSave = async () => {
    if (!selectedStage) {
      toast.error("Select a lead stage first");
      return;
    }
    setSaving(true);
    try {
      if (triggerMapping) {
        await stageMappingService.update(triggerMapping.id, { stage_key: selectedStage });
        toast.success("Trigger stage updated");
      } else {
        await stageMappingService.create({
          journey_id: journeyId,
          stage_key: selectedStage,
          name: `Trigger: ${selectedStage}`,
        });
        toast.success("Trigger stage configured");
      }
      if (onRefresh) onRefresh();
    } catch (err) {
      toast.error(err?.message || "Failed to save trigger stage");
    } finally {
      setSaving(false);
    }
  };

  const stageLabel = stages.find((s) => s.value === (triggerMapping?.stage_key || selectedStage))?.label || triggerMapping?.stage_key;

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-sm font-bold">Trigger Configuration</h3>
        <p className="text-xs text-muted-foreground">
          Select the lead stage that will trigger this journey.
        </p>
      </div>

      <Card className="rounded-xl border-border bg-card p-5">
        <div className="space-y-4">
          <div>
            <Label className="text-xs font-semibold">Current Trigger</Label>
            <p className="text-[11px] text-muted-foreground">
              Lead Stage
            </p>
          </div>

          <Select value={selectedStage} onValueChange={setSelectedStage}>
            <SelectTrigger className="w-full sm:max-w-xs">
              <SelectValue placeholder="Select Lead Stage" />
            </SelectTrigger>
            <SelectContent>
              {stages.map((s) => (
                <SelectItem key={s.value} value={s.value}>
                  {s.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <div className="flex items-center gap-2">
            <Button size="sm" onClick={handleSave} disabled={saving}>
              {saving && <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" />}
              Save Trigger
            </Button>
            {triggerMapping && (
              <span className="text-xs text-emerald-600">
                Trigger saved: {stageLabel}
              </span>
            )}
          </div>
        </div>
      </Card>

      {!triggerMapping && (
        <Card className="rounded-xl border-dashed border-border bg-card p-6 text-center text-sm text-muted-foreground">
          <Target className="mx-auto mb-2 h-5 w-5" />
          No trigger stage configured. Select a lead stage and click Save Trigger.
        </Card>
      )}
    </div>
  );
}

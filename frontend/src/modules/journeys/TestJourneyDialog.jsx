import { useState } from "react";
import { toast } from "sonner";
import { executionService } from "@/services/execution";
import { stageMappingService } from "@/services/stageMappings";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Loader2, Play } from "lucide-react";

export default function TestJourneyDialog({ open, onOpenChange, journeyId }) {
  const [leadId, setLeadId] = useState("");
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(null);

  const reset = () => {
    setLeadId("");
    setRunning(false);
    setResult(null);
    onOpenChange(false);
  };

  const handleRun = async () => {
    if (!leadId.trim()) {
      toast.error("Enter a Lead ID");
      return;
    }
    setRunning(true);
    setResult(null);
    try {
      const mappings = await stageMappingService.list({ journeyId });
      const stageKey = mappings?.[0]?.stage_key;
      if (!stageKey) {
        toast.error("Journey has no trigger stage configured");
        setRunning(false);
        return;
      }
      const res = await executionService.test({
        journey_id: journeyId,
        lead_id: parseInt(leadId, 10),
        stage_key: stageKey,
      });
      setResult(res);
      if (res.success) {
        toast.success("Test execution completed");
      } else {
        toast.error("Test execution failed");
      }
    } catch (err) {
      toast.error(err?.message || "Test execution failed");
      setResult({ success: false, error: err?.message });
    } finally {
      setRunning(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) reset(); }}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Test Journey</DialogTitle>
          <DialogDescription>
            Run a test execution using the journey's configured trigger stage.
            No external webhook is needed.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <div className="space-y-1.5">
            <Label htmlFor="test-lead-id">Lead ID</Label>
            <Input
              id="test-lead-id"
              type="number"
              value={leadId}
              onChange={(e) => setLeadId(e.target.value)}
              placeholder="e.g. 12345"
            />
            <p className="text-[11px] text-muted-foreground">
              Enter a numeric lead ID that exists in your system.
            </p>
          </div>

          {result && (
            <div className={`rounded-lg border p-3 text-sm ${result.success ? "border-emerald-500/30 bg-emerald-500/5 text-emerald-700" : "border-red-500/30 bg-red-500/5 text-red-700"}`}>
              <div className="font-semibold">{result.success ? "Execution completed" : "Execution failed"}</div>
              {result.trigger_stage_key && (
                <div className="mt-1 text-xs opacity-80">Trigger: {result.trigger_stage_key}</div>
              )}
              {result.error && (
                <div className="mt-1 text-xs opacity-80">{result.error}</div>
              )}
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={reset}>
            Cancel
          </Button>
          <Button onClick={handleRun} disabled={running}>
            {running ? (
              <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" />
            ) : (
              <Play className="mr-2 h-3.5 w-3.5" />
            )}
            Run
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

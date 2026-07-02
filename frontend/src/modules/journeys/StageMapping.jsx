import StatusBadge from "@/components/StatusBadge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Plus, Zap } from "lucide-react";

export default function StageMapping({ mappings = [], journeyName }) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold">Stage Mappings</h3>
          <p className="text-xs text-muted-foreground">
            Map JAWIS lead stages to trigger this journey
          </p>
        </div>
        <Button size="sm" variant="outline">
          <Plus className="mr-2 h-3.5 w-3.5" /> Add mapping
        </Button>
      </div>

      {mappings.length === 0 ? (
        <Card className="rounded-xl border-dashed border-border bg-card p-6 text-center text-sm text-muted-foreground">
          <Zap className="mx-auto mb-2 h-5 w-5" />
          No stage mappings configured for {journeyName}.
        </Card>
      ) : (
        <div className="space-y-2">
          {mappings.map((m) => (
            <Card key={m.id} className="flex items-center justify-between rounded-xl border-border bg-card p-4">
              <div className="flex items-center gap-3">
                <StatusBadge status={m.enabled ? "Active" : "Draft"} />
                <div>
                  <span className="text-sm font-semibold">{m.stageLabel}</span>
                  <span className="ml-2 text-xs text-muted-foreground">({m.stageKey})</span>
                </div>
              </div>
              <div className="flex items-center gap-3 text-xs text-muted-foreground">
                <span>Trigger: <span className="font-medium text-foreground">{m.trigger}</span></span>
                <span>Mode: <span className="font-medium text-foreground">{m.mode}</span></span>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

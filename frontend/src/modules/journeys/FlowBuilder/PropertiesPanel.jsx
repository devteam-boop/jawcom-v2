import { Card } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

export default function PropertiesPanel({ selectedNode }) {
  if (!selectedNode) {
    return (
      <aside className="border-l border-border bg-card/40 p-5">
        <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
          Select a node to edit its properties
        </div>
      </aside>
    );
  }

  return (
    <aside className="overflow-y-auto border-l border-border bg-card/40 p-5 scrollbar-thin">
      <div className="mb-4">
        <h3 className="text-sm font-bold">Node Settings</h3>
      </div>

      <Card className="mb-4 rounded-lg border-border bg-background p-3">
        <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Selected</div>
        <div className="mt-0.5 text-sm font-semibold">{selectedNode.type}</div>
        <div className="text-xs text-muted-foreground">{selectedNode.label}</div>
      </Card>

      <div className="space-y-3 text-sm">
        <div className="space-y-1.5">
          <Label>Label</Label>
          <Input defaultValue={selectedNode.label} />
        </div>

        <div className="space-y-1.5">
          <Label>Type</Label>
          <Select value={selectedNode.type} disabled>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value={selectedNode.type}>{selectedNode.type}</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
    </aside>
  );
}

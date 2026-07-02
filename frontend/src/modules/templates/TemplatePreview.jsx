import StatusBadge from "@/components/StatusBadge";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Copy, Archive, Play, XCircle, CheckCircle2 } from "lucide-react";

const STATUS_META = {
  Approved: { badge: "Active", tone: "success" },
  "In Review": { badge: "Open", tone: "info" },
  Pending: { badge: "Open", tone: "info" },
  Draft: { badge: "Draft", tone: "neutral" },
  Rejected: { badge: "Lost", tone: "danger" },
  Archived: { badge: "Closed", tone: "neutral" },
};

function Row({ label, value }) {
  return (
    <div className="flex items-center justify-between border-b border-border/60 pb-2 text-sm">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className="text-sm font-medium">{value}</span>
    </div>
  );
}

export default function TemplatePreview({ template, channel }) {
  if (!template) {
    return (
      <aside className="flex h-full items-center justify-center border-l border-border bg-card/40 p-5 text-sm text-muted-foreground">
        <FileText className="mr-2 h-4 w-4" /> Pick a template to preview
      </aside>
    );
  }

  const meta = STATUS_META[template.status] || STATUS_META.Draft;

  const variables = (template.preview?.match(/\{\{(\w+)\}\}/g) || []).map((v) => v.replace(/\{|\}/g, ""));

  return (
    <aside className="overflow-y-auto border-l border-border bg-card/40 p-5 scrollbar-thin">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-bold">Preview</h3>
        <StatusBadge status={meta.badge} tone={meta.tone} />
      </div>

      <Card className="rounded-lg border-border bg-background p-3">
        <div className="text-[10px] uppercase tracking-wider text-muted-foreground">{channel} · {template.language}</div>
        <div className="mt-1 text-sm font-semibold">{template.name}</div>
        <div className="mt-3 rounded-lg border border-border bg-secondary/30 p-3 font-mono text-xs leading-relaxed">
          {template.preview?.split("\n").map((line, i) => <div key={i}>{line}</div>)}
        </div>
      </Card>

      <Tabs defaultValue="vars" className="mt-4">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="vars" className="text-xs">Variables</TabsTrigger>
          <TabsTrigger value="meta" className="text-xs">Metadata</TabsTrigger>
        </TabsList>
        <TabsContent value="vars" className="mt-3 space-y-2">
          {variables.length === 0 ? (
            <div className="rounded-lg border border-dashed border-border p-3 text-center text-xs text-muted-foreground">
              No variables in this template
            </div>
          ) : (
            variables.map((v) => (
              <div key={v} className="flex items-center justify-between rounded-lg border border-border p-2.5">
                <span className="font-mono text-xs font-semibold">{`{{${v}}}`}</span>
                <Input defaultValue="sample" className="h-7 max-w-[140px] font-mono text-xs" />
              </div>
            ))
          )}
        </TabsContent>
        <TabsContent value="meta" className="mt-3 space-y-2">
          <Row label="Approval status" value={<StatusBadge status={meta.badge} tone={meta.tone} />} />
          <Row label="Version" value={template.version || "v1.0"} />
          <Row label="Language" value={template.language} />
          <Row label="Category" value={template.category} />
          <Row label="Last updated" value={template.lastEdited} />
        </TabsContent>
      </Tabs>

      <div className="mt-5 space-y-1.5">
        <div className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Actions</div>
        <div className="grid grid-cols-2 gap-1.5">
          <Button variant="outline" size="sm" className="h-8 text-xs"><Copy className="mr-1 h-3 w-3" /> Duplicate</Button>
          <Button variant="outline" size="sm" className="h-8 text-xs"><Archive className="mr-1 h-3 w-3" /> Archive</Button>
          <Button variant="outline" size="sm" className="h-8 text-xs"><Play className="mr-1 h-3 w-3" /> Test</Button>
          <Button variant="outline" size="sm" className="h-8 text-xs"><XCircle className="mr-1 h-3 w-3" /> Reject</Button>
          <Button size="sm" className="col-span-2 h-8 text-xs"><CheckCircle2 className="mr-1 h-3 w-3" /> Approve</Button>
        </div>
      </div>
    </aside>
  );
}

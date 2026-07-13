import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Trash2 } from "lucide-react";
import { templateService } from "@/services/templates";

const VARIABLE_PREVIEWS = {
  "lead.id": "1234",
  "lead.name": "John Doe",
  "lead.email": "john@example.com",
  "lead.phone": "+1234567890",
  "company.name": "Acme Corp",
  "company.industry": "Technology",
  "journey.name": "My Journey",
  "today": "2026-07-06",
  "now": "2026-07-06T12:00:00",
  "execution.id": "abc-123-def-456",
};

function previewTemplate(template) {
  if (!template || typeof template !== "string") return template;
  return template.replace(/\{\{([\w.]+)\}\}/g, (match, path) => {
    return VARIABLE_PREVIEWS[path] || match;
  });
}

function hasVariables(value) {
  if (!value || typeof value !== "string") return false;
  return /\{\{[\w.]+\}\}/.test(value);
}

function PreviewButton({ value }) {
  const [showPreview, setShowPreview] = useState(false);
  if (!hasVariables(value)) return null;
  return (
    <div className="mt-1">
      <Button
        type="button"
        variant="ghost"
        size="sm"
        className="h-5 px-2 text-[10px]"
        onClick={() => setShowPreview(!showPreview)}
      >
        {showPreview ? "Hide Preview" : "Preview"}
      </Button>
      {showPreview && (
        <div className="mt-1 rounded border border-border/50 bg-muted/30 px-2 py-1 text-xs text-muted-foreground">
          {previewTemplate(value)}
        </div>
      )}
    </div>
  );
}

function TemplateSelectField({ channel, value, onChange }) {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    setLoading(true);
    templateService
      .list({ channel })
      .then((data) => { if (active) setTemplates(data); })
      .catch(() => { if (active) setTemplates([]); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [channel]);

  const selected = templates.find((t) => t.id === value);

  // Passes both id and the resolved name up in one call (not two separate
  // onUpdateConfig calls) — the caller applies them as a single atomic
  // config update, avoiding a stale-closure race where a second update
  // built from the same pre-update `config` snapshot would clobber the
  // first (see PropertiesPanel's handleConfigChangeBatch).
  const handleChange = (id) => {
    const tpl = templates.find((t) => t.id === id);
    onChange({ template_id: id, template_name: tpl?.name || "" });
  };

  return (
    <div className="space-y-1.5">
      <Label>Template</Label>
      <Select value={value || undefined} onValueChange={handleChange}>
        <SelectTrigger>
          <SelectValue placeholder={loading ? "Loading templates…" : "Select a template"} />
        </SelectTrigger>
        <SelectContent>
          {!loading && templates.length === 0 ? (
            <div className="px-2 py-1.5 text-xs text-muted-foreground">
              No {channel} templates yet — create one in Template Library
            </div>
          ) : (
            templates.map((t) => (
              <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>
            ))
          )}
        </SelectContent>
      </Select>
      {selected && <PreviewButton value={selected.content} />}
    </div>
  );
}

function ConfigFields({ nodeType, config, onUpdateConfig, onUpdateConfigBatch }) {
  switch (nodeType) {
    case "trigger":
      return (
        <p className="text-xs text-muted-foreground">
          Trigger nodes are read-only. The journey starts here.
        </p>
      );

    case "wait":
      return (
        <>
          <div className="space-y-1.5">
            <Label>Duration</Label>
            <Input
              type="number"
              min="0"
              placeholder="e.g. 2"
              value={config.duration ?? ""}
              onChange={(e) =>
                onUpdateConfig("duration", e.target.value ? parseInt(e.target.value) : "")
              }
            />
          </div>
          <div className="space-y-1.5">
            <Label>Unit</Label>
            <Select
              value={config.unit || "days"}
              onValueChange={(v) => onUpdateConfig("unit", v)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="minutes">Minutes</SelectItem>
                <SelectItem value="hours">Hours</SelectItem>
                <SelectItem value="days">Days</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </>
      );

    case "delay":
      return (
        <>
          <div className="space-y-1.5">
            <Label>Duration</Label>
            <Input
              type="number"
              min="0"
              placeholder="e.g. 30"
              value={config.duration ?? ""}
              onChange={(e) =>
                onUpdateConfig("duration", e.target.value ? parseInt(e.target.value) : "")
              }
            />
          </div>
          <div className="space-y-1.5">
            <Label>Unit</Label>
            <Select
              value={config.unit || "minutes"}
              onValueChange={(v) => onUpdateConfig("unit", v)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="minutes">Minutes</SelectItem>
                <SelectItem value="hours">Hours</SelectItem>
                <SelectItem value="days">Days</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </>
      );

    case "send_whatsapp":
      return (
        <>
          <TemplateSelectField
            channel="whatsapp"
            value={config.template_id || ""}
            onChange={onUpdateConfigBatch}
          />
        </>
      );

    case "send_email":
      return (
        <>
          <div className="space-y-1.5">
            <Label>Subject</Label>
            <Input
              placeholder="e.g. Welcome to our service (leave blank to use the template's subject)"
              value={config.subject || ""}
              onChange={(e) => onUpdateConfig("subject", e.target.value)}
            />
            <PreviewButton value={config.subject || ""} />
          </div>
          <TemplateSelectField
            channel="email"
            value={config.template_id || ""}
            onChange={onUpdateConfigBatch}
          />
        </>
      );

    case "notification":
      return (
        <>
          <div className="space-y-1.5">
            <Label>Title</Label>
            <Input
              placeholder="e.g. New Lead Alert"
              value={config.title || ""}
              onChange={(e) => onUpdateConfig("title", e.target.value)}
            />
            <PreviewButton value={config.title || ""} />
          </div>
          <div className="space-y-1.5">
            <Label>Message</Label>
            <Textarea
              placeholder="e.g. A new lead has entered the journey"
              value={config.message || ""}
              onChange={(e) => onUpdateConfig("message", e.target.value)}
            />
            <PreviewButton value={config.message || ""} />
          </div>
        </>
      );

    case "condition":
      return (
        <>
          <div className="space-y-1.5">
            <Label>Field</Label>
            <Input
              placeholder="e.g. lead.stage"
              value={config.field || ""}
              onChange={(e) => onUpdateConfig("field", e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label>Operator</Label>
            <Select
              value={config.operator || "equals"}
              onValueChange={(v) => onUpdateConfig("operator", v)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="equals">Equals</SelectItem>
                <SelectItem value="not_equals">Not Equals</SelectItem>
                <SelectItem value="greater_than">Greater Than</SelectItem>
                <SelectItem value="less_than">Less Than</SelectItem>
                <SelectItem value="contains">Contains</SelectItem>
                <SelectItem value="starts_with">Starts With</SelectItem>
                <SelectItem value="ends_with">Ends With</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label>Value</Label>
            <Input
              placeholder="e.g. won"
              value={config.value || ""}
              onChange={(e) => onUpdateConfig("value", e.target.value)}
            />
            <PreviewButton value={config.value || ""} />
          </div>
        </>
      );

    case "update_lead":
      return (
        <>
          <div className="space-y-1.5">
            <Label>Lead Field</Label>
            <Input
              placeholder="e.g. lead.phone"
              value={config.lead_field || ""}
              onChange={(e) => onUpdateConfig("lead_field", e.target.value)}
            />
            <PreviewButton value={config.lead_field || ""} />
          </div>
          <div className="space-y-1.5">
            <Label>Value</Label>
            <Input
              placeholder="e.g. +1234567890"
              value={config.value || ""}
              onChange={(e) => onUpdateConfig("value", e.target.value)}
            />
            <PreviewButton value={config.value || ""} />
          </div>
        </>
      );

    case "update_company":
      return (
        <>
          <div className="space-y-1.5">
            <Label>Company Field</Label>
            <Input
              placeholder="e.g. company.industry"
              value={config.company_field || ""}
              onChange={(e) => onUpdateConfig("company_field", e.target.value)}
            />
            <PreviewButton value={config.company_field || ""} />
          </div>
          <div className="space-y-1.5">
            <Label>Value</Label>
            <Input
              placeholder="e.g. Technology"
              value={config.value || ""}
              onChange={(e) => onUpdateConfig("value", e.target.value)}
            />
            <PreviewButton value={config.value || ""} />
          </div>
        </>
      );

    case "assign_owner":
      return (
        <>
          <div className="space-y-1.5">
            <Label>Owner ID</Label>
            <Input
              placeholder="e.g. user_abc123"
              value={config.owner_id || ""}
              onChange={(e) => onUpdateConfig("owner_id", e.target.value)}
            />
            <PreviewButton value={config.owner_id || ""} />
          </div>
        </>
      );

    case "change_lead_stage":
      return (
        <>
          <div className="space-y-1.5">
            <Label>Target Stage</Label>
            <Input
              placeholder="e.g. qualified"
              value={config.target_stage || ""}
              onChange={(e) => onUpdateConfig("target_stage", e.target.value)}
            />
            <PreviewButton value={config.target_stage || ""} />
          </div>
        </>
      );

    case "create_crm_task":
      return (
        <>
          <div className="space-y-1.5">
            <Label>Title</Label>
            <Input
              placeholder="e.g. Follow up with lead"
              value={config.title || ""}
              onChange={(e) => onUpdateConfig("title", e.target.value)}
            />
            <PreviewButton value={config.title || ""} />
          </div>
          <div className="space-y-1.5">
            <Label>Description</Label>
            <Textarea
              placeholder="e.g. Call the lead to discuss proposal"
              value={config.description || ""}
              onChange={(e) => onUpdateConfig("description", e.target.value)}
            />
            <PreviewButton value={config.description || ""} />
          </div>
          <div className="space-y-1.5">
            <Label>Due In (Days)</Label>
            <Input
              type="number"
              min="0"
              placeholder="e.g. 7"
              value={config.due_in_days ?? ""}
              onChange={(e) =>
                onUpdateConfig("due_in_days", e.target.value ? parseInt(e.target.value) : "")
              }
            />
          </div>
        </>
      );

    case "create_note":
      return (
        <>
          <div className="space-y-1.5">
            <Label>Note</Label>
            <Textarea
              placeholder="e.g. Lead expressed interest in premium plan"
              value={config.note || ""}
              onChange={(e) => onUpdateConfig("note", e.target.value)}
            />
            <PreviewButton value={config.note || ""} />
          </div>
        </>
      );

    case "approval":
      return (
        <>
          <div className="space-y-1.5">
            <Label>Approver</Label>
            <Input
              placeholder="e.g. manager@company.com"
              value={config.approver || ""}
              onChange={(e) => onUpdateConfig("approver", e.target.value)}
            />
            <PreviewButton value={config.approver || ""} />
          </div>
          <div className="space-y-1.5">
            <Label>Approval Title</Label>
            <Input
              placeholder="e.g. Approve discount for {{lead.name}}"
              value={config.title || ""}
              onChange={(e) => onUpdateConfig("title", e.target.value)}
            />
            <PreviewButton value={config.title || ""} />
          </div>
          <div className="space-y-1.5">
            <Label>Description</Label>
            <Textarea
              placeholder="e.g. Lead has requested a 20% discount on premium plan"
              value={config.description || ""}
              onChange={(e) => onUpdateConfig("description", e.target.value)}
            />
            <PreviewButton value={config.description || ""} />
          </div>
          <div className="space-y-1.5">
            <Label>Timeout (seconds)</Label>
            <Input
              type="number"
              min="0"
              placeholder="e.g. 86400"
              value={config.timeout ?? ""}
              onChange={(e) =>
                onUpdateConfig("timeout", e.target.value ? parseInt(e.target.value) : "")
              }
            />
          </div>
          <div className="space-y-1.5">
            <Label>Approval Type</Label>
            <Select
              value={config.approval_type || "approve_reject"}
              onValueChange={(v) => onUpdateConfig("approval_type", v)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="approve_reject">Approve / Reject</SelectItem>
                <SelectItem value="single_approve">Single Approve</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </>
      );

    case "manual_task":
      return (
        <>
          <div className="space-y-1.5">
            <Label>Assignee</Label>
            <Input
              placeholder="e.g. john.doe@company.com"
              value={config.assignee || ""}
              onChange={(e) => onUpdateConfig("assignee", e.target.value)}
            />
            <PreviewButton value={config.assignee || ""} />
          </div>
          <div className="space-y-1.5">
            <Label>Task Title</Label>
            <Input
              placeholder="e.g. Review proposal for {{lead.name}}"
              value={config.title || ""}
              onChange={(e) => onUpdateConfig("title", e.target.value)}
            />
            <PreviewButton value={config.title || ""} />
          </div>
          <div className="space-y-1.5">
            <Label>Description</Label>
            <Textarea
              placeholder="e.g. Prepare and send a custom proposal to the lead"
              value={config.description || ""}
              onChange={(e) => onUpdateConfig("description", e.target.value)}
            />
            <PreviewButton value={config.description || ""} />
          </div>
          <div className="space-y-1.5">
            <Label>Due Date</Label>
            <Input
              placeholder="e.g. 2026-07-13"
              value={config.due_date || ""}
              onChange={(e) => onUpdateConfig("due_date", e.target.value)}
            />
            <PreviewButton value={config.due_date || ""} />
          </div>
          <div className="space-y-1.5">
            <Label>Priority</Label>
            <Select
              value={config.priority || "medium"}
              onValueChange={(v) => onUpdateConfig("priority", v)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="low">Low</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="urgent">Urgent</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </>
      );

    case "end":
      return (
        <p className="text-xs text-muted-foreground">
          End node is read-only. The journey stops here.
        </p>
      );

    default:
      return null;
  }
}

export default function PropertiesPanel({ selectedNode, onUpdateNode, onDeleteNode }) {
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);

  if (!selectedNode) {
    return (
      <aside className="border-l border-border bg-card/40 p-5">
        <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
          Select a node to edit its properties
        </div>
      </aside>
    );
  }

  const config = selectedNode.data.config || {};
  const isTrigger = selectedNode.type === "trigger";

  const handleLabelChange = (e) => {
    onUpdateNode(selectedNode.id, { label: e.target.value });
  };

  const handleConfigChange = (key, value) => {
    onUpdateNode(selectedNode.id, {
      config: { ...config, [key]: value },
    });
  };

  // Applies multiple config keys in one atomic update (vs. calling
  // handleConfigChange twice, which would each build off the same
  // pre-update `config` snapshot and the second call would clobber the
  // first's change) — used by TemplateSelectField to set template_id and
  // template_name together.
  const handleConfigChangeBatch = (updates) => {
    onUpdateNode(selectedNode.id, {
      config: { ...config, ...updates },
    });
  };

  const handleConfirmDelete = () => {
    onDeleteNode(selectedNode.id);
    setDeleteConfirmOpen(false);
  };

  return (
    <aside className="overflow-y-auto border-l border-border bg-card/40 p-5 scrollbar-thin">
      <div className="mb-4">
        <h3 className="text-sm font-bold">Node Settings</h3>
      </div>

      <Card className="mb-4 rounded-lg border-border bg-background p-3">
        <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Selected</div>
        <div className="mt-0.5 text-sm font-semibold">{selectedNode.type}</div>
        <div className="text-xs text-muted-foreground">{selectedNode.data.label}</div>
      </Card>

      <div className="space-y-3 text-sm">
        <div className="space-y-1.5">
          <Label>Label</Label>
          <Input
            value={selectedNode.data.label}
            onChange={handleLabelChange}
          />
        </div>

        <hr className="border-border" />

        <div className="space-y-3">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Configuration
          </h4>
          <ConfigFields
            nodeType={selectedNode.type}
            config={config}
            onUpdateConfig={handleConfigChange}
            onUpdateConfigBatch={handleConfigChangeBatch}
          />
        </div>

        {!isTrigger && (
          <>
            <hr className="border-border" />
            <Button
              variant="destructive"
              size="sm"
              className="w-full"
              onClick={() => setDeleteConfirmOpen(true)}
              data-testid="node-delete"
            >
              <Trash2 className="mr-2 h-3.5 w-3.5" /> Delete Node
            </Button>
          </>
        )}
      </div>

      <Dialog open={deleteConfirmOpen} onOpenChange={setDeleteConfirmOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Node?</DialogTitle>
            <DialogDescription>
              This removes "{selectedNode.data.label}" and every connection to and from it. The
              nodes on either side will be left disconnected — reconnect them afterward if the
              flow needs to continue past this point. This cannot be undone (until you Save again).
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteConfirmOpen(false)}>Cancel</Button>
            <Button variant="destructive" onClick={handleConfirmDelete} data-testid="node-delete-confirm">
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </aside>
  );
}

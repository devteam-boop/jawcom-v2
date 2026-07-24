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
import { formatDateTime } from "@/lib/dateFormat";

const UNIT_SECONDS = { minutes: 60, hours: 3600, days: 86400, weeks: 604800 };
const CONDITION_OPERATORS = [
  ["equals", "Equals"],
  ["not_equals", "Not Equals"],
  ["greater_than", "Greater Than"],
  ["less_than", "Less Than"],
  ["contains", "Contains"],
  ["starts_with", "Starts With"],
  ["ends_with", "Ends With"],
];

function applyOffset(base, value, unit) {
  return new Date(base.getTime() + (value || 0) * (UNIT_SECONDS[unit] || 60) * 1000);
}

function SchedulePreview({ children }) {
  return (
    <div className="mt-1 rounded border border-border/50 bg-muted/30 px-2 py-1 text-xs text-muted-foreground">
      {children}
    </div>
  );
}

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
  // Standardized 18-field variable contract — bare names (as used directly
  // in template bodies, e.g. {{building_name}}), matching the sample values
  // DummyLeadProvider returns at execution time (see
  // backend/app/execution/providers/lead_provider.py) so this preview
  // reflects what actually resolves at send time, not a placeholder.
  first_name: "John",
  last_name: "Doe",
  company: "Acme Corp",
  city: "Lucknow",
  seats: "2",
  plan_type: "2BHK",
  building_name: "Acme Business Tower",
  building_id: "BLD-1042",
  price: "1.2Cr",
  move_in_date: "2026-09-15",
  tour_datetime: "2026-08-01 11:00 AM",
  agent_name: "Jane Agent",
  options_link: "https://example.com/options/42",
  proposal_link: "https://example.com/proposal/42",
  map_link: "https://maps.example.com/acme-tower",
  email: "john.doe@example.com",
  phone: "+1234567890",
  assigned_to: "Jane Agent",
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
  // Condition's Operator <Select> below displays "equals" via a
  // `config.operator || "equals"` fallback when nothing has been chosen yet
  // — that fallback is display-only and was never written back into the
  // node's persisted config, so a condition node whose dropdown was never
  // explicitly touched serialized with no "operator" key at all (despite
  // showing "Equals" in the UI), and flow_validation_service.py's
  // `if not config.get("operator")` correctly flagged it as missing. This
  // seeds the real default into config as soon as a condition node with no
  // operator is shown, so what's displayed always matches what's persisted.
  useEffect(() => {
    if (nodeType === "condition" && !config.operator) {
      onUpdateConfig("operator", "equals");
    }
  }, [nodeType, config.operator, onUpdateConfig]);

  // Same display-default-vs-persisted-default bug class as Condition's
  // Operator above, reproduced by two new fields: Wait's Operator <Select>
  // (shown, via a `config.operator || "equals"` fallback, whenever wait_type
  // is stage_changed/field_condition — flow_validation_service.py requires
  // it present with no default) and Delay's Offset Unit <Select> (shown,
  // via `config.offset_unit || "hours"`, whenever mode is
  // relative_to_lead_date — same strict requirement). Both are seeded here
  // the same way, only while the relevant mode/wait_type is actually active.
  useEffect(() => {
    if (
      nodeType === "wait"
      && (config.wait_type === "stage_changed" || config.wait_type === "field_condition")
      && !config.operator
    ) {
      onUpdateConfig("operator", "equals");
    }
  }, [nodeType, config.wait_type, config.operator, onUpdateConfig]);

  useEffect(() => {
    if (nodeType === "delay" && config.mode === "relative_to_lead_date" && !config.offset_unit) {
      onUpdateConfig("offset_unit", "hours");
    }
  }, [nodeType, config.mode, config.offset_unit, onUpdateConfig]);

  switch (nodeType) {
    case "trigger":
      return (
        <p className="text-xs text-muted-foreground">
          Trigger nodes are read-only. The journey starts here.
        </p>
      );

    case "wait": {
      const waitType = config.wait_type || "duration";
      let waitDescription = "";
      if (waitType === "duration") {
        waitDescription = `Wait until ${config.duration || "?"} ${config.unit || "days"} have elapsed`;
      } else if (waitType === "specific_datetime") {
        waitDescription = config.target_lead_field
          ? `Wait until lead.${config.target_lead_field}`
          : config.target_datetime
          ? `Wait until ${formatDateTime(new Date(config.target_datetime))}`
          : "Wait until a specific date/time (not yet configured)";
      } else if (waitType === "replied") {
        waitDescription = `Wait until lead replied (${config.channel || "whatsapp"})`;
      } else if (waitType === "stage_changed" || waitType === "field_condition") {
        const opLabel = CONDITION_OPERATORS.find(([v]) => v === (config.operator || "equals"))?.[1] || "Equals";
        waitDescription = `Wait until ${config.field || "?"} ${opLabel} ${config.value || "?"}`;
      } else if (waitType === "manual_approval") {
        waitDescription = `Wait until manual approval${config.title ? `: ${config.title}` : ""}`;
      } else if (waitType === "webhook_event") {
        waitDescription = `Wait until external event '${config.event_key || "?"}'`;
      }

      return (
        <>
          <div className="space-y-1.5">
            <Label>Wait Type</Label>
            <Select
              value={waitType}
              onValueChange={(v) => onUpdateConfigBatch({ wait_type: v })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="duration">Duration</SelectItem>
                <SelectItem value="specific_datetime">Specific Date/Time</SelectItem>
                <SelectItem value="replied">Lead Replied</SelectItem>
                <SelectItem value="stage_changed">Stage Changes</SelectItem>
                <SelectItem value="field_condition">Lead Field Changes</SelectItem>
                <SelectItem value="manual_approval">Manual Approval</SelectItem>
                <SelectItem value="webhook_event">External Webhook/Event</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {waitType === "duration" && (
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
                    <SelectItem value="weeks">Weeks</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </>
          )}

          {waitType === "specific_datetime" && (
            <>
              <div className="space-y-1.5">
                <Label>Lead Date Field (optional)</Label>
                <Input
                  placeholder="e.g. tour_datetime"
                  value={config.target_lead_field || ""}
                  onChange={(e) => onUpdateConfig("target_lead_field", e.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <Label>Or a literal Date/Time</Label>
                <Input
                  type="datetime-local"
                  value={config.target_datetime || ""}
                  onChange={(e) => onUpdateConfig("target_datetime", e.target.value)}
                  disabled={!!config.target_lead_field}
                />
              </div>
            </>
          )}

          {waitType === "replied" && (
            <div className="space-y-1.5">
              <Label>Channel</Label>
              <Select
                value={config.channel || "whatsapp"}
                onValueChange={(v) => onUpdateConfig("channel", v)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="whatsapp">WhatsApp</SelectItem>
                  <SelectItem value="email">Email</SelectItem>
                </SelectContent>
              </Select>
            </div>
          )}

          {(waitType === "stage_changed" || waitType === "field_condition") && (
            <>
              <div className="space-y-1.5">
                <Label>Field</Label>
                <Input
                  placeholder={waitType === "stage_changed" ? "e.g. stage" : "e.g. visit_completed"}
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
                    {CONDITION_OPERATORS.map(([v, label]) => (
                      <SelectItem key={v} value={v}>{label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label>Value</Label>
                <Input
                  placeholder="e.g. qualified"
                  value={config.value || ""}
                  onChange={(e) => onUpdateConfig("value", e.target.value)}
                />
              </div>
            </>
          )}

          {waitType === "manual_approval" && (
            <>
              <div className="space-y-1.5">
                <Label>Approver</Label>
                <Input
                  placeholder="e.g. manager@company.com"
                  value={config.approver || ""}
                  onChange={(e) => onUpdateConfig("approver", e.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <Label>Approval Title</Label>
                <Input
                  placeholder="e.g. Approve discount for {{lead.name}}"
                  value={config.title || ""}
                  onChange={(e) => onUpdateConfig("title", e.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <Label>Description</Label>
                <Textarea
                  placeholder="e.g. Lead has requested a 20% discount"
                  value={config.description || ""}
                  onChange={(e) => onUpdateConfig("description", e.target.value)}
                />
              </div>
            </>
          )}

          {waitType === "webhook_event" && (
            <div className="space-y-1.5">
              <Label>Event Key</Label>
              <Input
                placeholder="e.g. payment_confirmed"
                value={config.event_key || ""}
                onChange={(e) => onUpdateConfig("event_key", e.target.value)}
              />
            </div>
          )}

          <SchedulePreview>{waitDescription}</SchedulePreview>
        </>
      );
    }

    case "delay": {
      const mode = config.mode || "fixed";
      const now = new Date();
      let delayPreview = null;
      if (mode === "fixed" && config.duration) {
        const executesAt = applyOffset(now, config.duration, config.unit || "minutes");
        delayPreview = (
          <>Current Time {formatDateTime(now)} → Executes {formatDateTime(executesAt)}</>
        );
      } else if (mode === "relative_to_lead_date" && config.lead_date_field) {
        // Illustrative example only — the actual lead's date isn't known
        // inside the builder. Uses a fixed sample anchor (3 days from now),
        // same convention as this panel's existing {{variable}} previews
        // (see VARIABLE_PREVIEWS above).
        const sampleLeadDate = applyOffset(now, 3, "days");
        const executesAt = applyOffset(sampleLeadDate, config.offset_value ?? 0, config.offset_unit || "hours");
        delayPreview = (
          <>Example — {config.lead_date_field} {formatDateTime(sampleLeadDate)} → Executes {formatDateTime(executesAt)}</>
        );
      }

      return (
        <>
          <div className="space-y-1.5">
            <Label>Mode</Label>
            <Select
              value={mode}
              onValueChange={(v) => onUpdateConfigBatch({ mode: v })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="fixed">Fixed Delay</SelectItem>
                <SelectItem value="relative_to_lead_date">Relative to Lead Date</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {mode === "fixed" && (
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
                    <SelectItem value="weeks">Weeks</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </>
          )}

          {mode === "relative_to_lead_date" && (
            <>
              <div className="space-y-1.5">
                <Label>Lead Date Field</Label>
                <Input
                  placeholder="e.g. tour_datetime, move_in_date"
                  value={config.lead_date_field || ""}
                  onChange={(e) => onUpdateConfig("lead_date_field", e.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <Label>Offset (use negative for "before")</Label>
                <Input
                  type="number"
                  placeholder="e.g. -24"
                  value={config.offset_value ?? ""}
                  onChange={(e) =>
                    onUpdateConfig("offset_value", e.target.value ? parseInt(e.target.value) : "")
                  }
                />
              </div>
              <div className="space-y-1.5">
                <Label>Offset Unit</Label>
                <Select
                  value={config.offset_unit || "hours"}
                  onValueChange={(v) => onUpdateConfig("offset_unit", v)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="minutes">Minutes</SelectItem>
                    <SelectItem value="hours">Hours</SelectItem>
                    <SelectItem value="days">Days</SelectItem>
                    <SelectItem value="weeks">Weeks</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </>
          )}

          {delayPreview && <SchedulePreview>{delayPreview}</SchedulePreview>}
        </>
      );
    }

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

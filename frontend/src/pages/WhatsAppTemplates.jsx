import { useEffect, useMemo, useState } from "react";
import PageHeader from "@/components/PageHeader";
import StatusBadge from "@/components/StatusBadge";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
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
import { whatsappTemplateService } from "@/services/whatsappTemplates";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import {
  Plus,
  RefreshCw,
  Send,
  Trash2,
  MessageCircle,
  CheckCircle2,
  Clock,
  XCircle,
} from "lucide-react";

const CATEGORIES = ["MARKETING", "UTILITY", "AUTHENTICATION"];
const HEADER_TYPES = [
  { value: "NONE", label: "No header" },
  { value: "TEXT", label: "Text" },
  { value: "IMAGE", label: "Image (stub — not sendable yet)" },
  { value: "VIDEO", label: "Video (stub — not sendable yet)" },
  { value: "DOCUMENT", label: "Document (stub — not sendable yet)" },
];
const SUBMITTED_STATUSES = ["DRAFT", "PENDING", "REJECTED"];

const STATUS_TONE = {
  APPROVED: "success",
  PENDING: "warning",
  DRAFT: "neutral",
  REJECTED: "danger",
  PAUSED: "warning",
  DISABLED: "danger",
};

function extractVariables(body = "") {
  const set = new Set();
  const re = /\{\{\s*(\d+)\s*\}\}/g;
  let m;
  while ((m = re.exec(body)) !== null) set.add(m[1]);
  return Array.from(set).sort((a, b) => Number(a) - Number(b));
}

function renderWithExamples(text, variables, examples) {
  if (!text) return text;
  return text.replace(/\{\{\s*(\d+)\s*\}\}/g, (match, n) => {
    const idx = variables.indexOf(n);
    return idx >= 0 && examples[idx] ? examples[idx] : match;
  });
}

const EMPTY_FORM = {
  template_name: "",
  category: "UTILITY",
  language: "en_US",
  header_type: "NONE",
  header_text: "",
  header_media_url: "",
  body: "",
  footer: "",
  buttons: [],
  examples: [],
};

export default function WhatsAppTemplates() {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [syncStatus, setSyncStatus] = useState({ last_synced_at: null, last_error: null });
  const [syncing, setSyncing] = useState(false);
  const [panel, setPanel] = useState("approved");
  const [submittingId, setSubmittingId] = useState(null);

  const [formOpen, setFormOpen] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);

  const refetch = async () => {
    try {
      setLoading(true);
      const [list, status] = await Promise.all([
        whatsappTemplateService.list(),
        whatsappTemplateService.syncStatus(),
      ]);
      setTemplates(list);
      setSyncStatus(status);
    } catch (err) {
      toast.error(err?.body?.detail || err.message || "Failed to load WhatsApp templates");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { refetch(); }, []);

  // Part 4 — same table, split by status filter, not two backing tables.
  const approved = useMemo(() => templates.filter((t) => t.status === "APPROVED"), [templates]);
  const submitted = useMemo(
    () => templates.filter((t) => SUBMITTED_STATUSES.includes(t.status)),
    [templates]
  );

  const handleSync = async () => {
    setSyncing(true);
    try {
      const result = await whatsappTemplateService.sync();
      toast.success(
        `Sync complete — scanned ${result.scanned}, created ${result.created}, updated ${result.updated}, unchanged ${result.unchanged}`
      );
      await refetch();
    } catch (err) {
      toast.error(err?.body?.detail || err.message || "Sync failed");
    } finally {
      setSyncing(false);
    }
  };

  const handleSubmit = async (template) => {
    setSubmittingId(template.id);
    try {
      await whatsappTemplateService.submit(template.id);
      toast.success(`Submitted to Meta — ${template.template_name} is now PENDING review`);
      await refetch();
    } catch (err) {
      // Real Meta error (malformed/restricted/expired/permission), surfaced
      // verbatim — status is left as DRAFT server-side, never faked.
      toast.error(err?.body?.detail || err.message || "Meta rejected the submission");
    } finally {
      setSubmittingId(null);
    }
  };

  const openCreate = () => {
    setForm(EMPTY_FORM);
    setFormOpen(true);
  };

  const updateExample = (index, value) => {
    setForm((f) => {
      const examples = [...f.examples];
      examples[index] = value;
      return { ...f, examples };
    });
  };

  const addButton = () => {
    setForm((f) => ({ ...f, buttons: [...f.buttons, { type: "QUICK_REPLY", text: "" }] }));
  };
  const removeButton = (index) => {
    setForm((f) => ({ ...f, buttons: f.buttons.filter((_, i) => i !== index) }));
  };
  const updateButton = (index, patch) => {
    setForm((f) => {
      const buttons = [...f.buttons];
      buttons[index] = { ...buttons[index], ...patch };
      return { ...f, buttons };
    });
  };

  const bodyVariables = useMemo(() => extractVariables(form.body), [form.body]);

  const handleSave = async () => {
    if (!form.template_name.trim() || !form.language.trim() || !form.body.trim()) {
      toast.error("Name, language, and body are required");
      return;
    }
    setSaving(true);
    try {
      const payload = {
        template_name: form.template_name.trim(),
        category: form.category,
        language: form.language.trim(),
        header_type: form.header_type === "NONE" ? null : form.header_type,
        header_text: form.header_type === "TEXT" ? form.header_text : null,
        header_media_url: form.header_type !== "NONE" && form.header_type !== "TEXT" ? form.header_media_url : null,
        body: form.body,
        footer: form.footer || null,
        buttons: form.buttons.filter((b) => b.text?.trim()),
        examples: bodyVariables.map((_, i) => form.examples[i] || ""),
      };
      // Saves locally AND immediately submits to Meta — the response
      // status tells us which actually happened; the row is created and
      // visible in the panel either way, so both branches still refetch.
      const created = await whatsappTemplateService.create(payload);
      if (created.status === "PENDING") {
        toast.success(`Submitted to Meta — ${created.template_name} is now PENDING review`);
      } else if (created.rejection_reason) {
        toast.error(`Saved as draft, but Meta submission failed: ${created.rejection_reason}`);
      } else {
        toast.success("Draft saved");
      }
      setFormOpen(false);
      await refetch();
    } catch (err) {
      toast.error(err?.body?.detail || err.message || "Failed to save template");
    } finally {
      setSaving(false);
    }
  };

  const list = panel === "approved" ? approved : submitted;

  return (
    <div data-testid="page-whatsapp-templates" className="flex h-full min-h-0 flex-col">
      <PageHeader
        title="WhatsApp Business Templates"
        description="Draft locally, submit to Meta for review, and track approval — Meta is the only source of APPROVED status."
        actions={
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={handleSync}
              disabled={syncing}
              data-testid="wa-sync-now"
            >
              <RefreshCw className={cn("mr-2 h-3.5 w-3.5", syncing && "animate-spin")} /> Sync Now
            </Button>
            <Button size="sm" onClick={openCreate} data-testid="wa-new-template">
              <Plus className="mr-2 h-3.5 w-3.5" /> New template
            </Button>
          </div>
        }
      />

      <div className="flex items-center justify-between px-4 py-2 text-xs text-muted-foreground md:px-8">
        <span>
          Last synced:{" "}
          {syncStatus.last_synced_at ? new Date(syncStatus.last_synced_at).toLocaleString() : "never"}
        </span>
        {syncStatus.last_error && (
          <span className="flex items-center gap-1 text-rose-600 dark:text-rose-400">
            <XCircle className="h-3.5 w-3.5" /> Last sync error: {syncStatus.last_error}
          </span>
        )}
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-thin p-4 md:p-8">
        <Tabs value={panel} onValueChange={setPanel}>
          <TabsList data-testid="wa-panel-tabs">
            <TabsTrigger value="approved" data-testid="wa-panel-approved">
              <CheckCircle2 className="mr-1.5 h-3.5 w-3.5" /> Approved (from Meta) · {approved.length}
            </TabsTrigger>
            <TabsTrigger value="submitted" data-testid="wa-panel-submitted">
              <Clock className="mr-1.5 h-3.5 w-3.5" /> Submitted / In Review · {submitted.length}
            </TabsTrigger>
          </TabsList>

          <TabsContent value={panel} className="mt-4">
            {loading ? (
              <div className="flex items-center justify-center p-12 text-sm text-muted-foreground">Loading…</div>
            ) : list.length === 0 ? (
              <div className="rounded-xl border border-dashed border-border p-8 text-center text-sm text-muted-foreground">
                {panel === "approved"
                  ? "No approved templates yet. Approvals only ever come from Meta (webhook or Sync Now)."
                  : "Nothing in review. Create a draft and submit it to Meta."}
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
                {list.map((t) => (
                  <TemplateRow
                    key={t.id}
                    template={t}
                    onSubmit={handleSubmit}
                    submitting={submittingId === t.id}
                  />
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>

      {/* Create draft dialog (Part 1) */}
      <Dialog open={formOpen} onOpenChange={setFormOpen}>
        <DialogContent className="max-h-[90vh] max-w-3xl overflow-y-auto">
          <DialogHeader>
            <DialogTitle>New WhatsApp Template</DialogTitle>
            <DialogDescription>
              Saved locally, then immediately submitted to Meta for review. If Meta rejects it, it stays
              here as a Draft with the real error shown so you can fix and resubmit. Use{" "}
              <code>{"{{1}}"}</code>, <code>{"{{2}}"}</code>… in the body for variables.
            </DialogDescription>
          </DialogHeader>

          <div className="grid grid-cols-1 gap-6 py-2 lg:grid-cols-2">
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label>Name</Label>
                  <Input
                    value={form.template_name}
                    onChange={(e) => setForm({ ...form, template_name: e.target.value })}
                    placeholder="e.g. order_confirmation"
                  />
                </div>
                <div className="space-y-1.5">
                  <Label>Language</Label>
                  <Input
                    value={form.language}
                    onChange={(e) => setForm({ ...form, language: e.target.value })}
                    placeholder="e.g. en_US"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label>Category</Label>
                  <Select value={form.category} onValueChange={(v) => setForm({ ...form, category: v })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {CATEGORIES.map((c) => <SelectItem key={c} value={c}>{c}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1.5">
                  <Label>Header</Label>
                  <Select value={form.header_type} onValueChange={(v) => setForm({ ...form, header_type: v })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {HEADER_TYPES.map((h) => <SelectItem key={h.value} value={h.value}>{h.label}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {form.header_type === "TEXT" && (
                <div className="space-y-1.5">
                  <Label>Header text</Label>
                  <Input
                    value={form.header_text}
                    onChange={(e) => setForm({ ...form, header_text: e.target.value })}
                    placeholder="e.g. Your order is confirmed"
                  />
                </div>
              )}
              {form.header_type !== "NONE" && form.header_type !== "TEXT" && (
                <div className="space-y-1.5">
                  <Label>Media source URL (stub)</Label>
                  <Input
                    value={form.header_media_url}
                    onChange={(e) => setForm({ ...form, header_media_url: e.target.value })}
                    placeholder="Saved for later — Submit to Meta will reject non-text headers today"
                  />
                  <p className="text-xs text-amber-600 dark:text-amber-400">
                    Media header upload isn't implemented yet — this draft can be saved, but submitting it
                    to Meta will be rejected until media handle upload exists.
                  </p>
                </div>
              )}

              <div className="space-y-1.5">
                <Label>Body</Label>
                <Textarea
                  value={form.body}
                  onChange={(e) => setForm({ ...form, body: e.target.value })}
                  placeholder={"e.g. Hi {{1}}, your order {{2}} has shipped."}
                  rows={5}
                  className="font-mono text-xs"
                />
              </div>

              <div className="space-y-1.5">
                <Label>Footer (optional)</Label>
                <Input
                  value={form.footer}
                  onChange={(e) => setForm({ ...form, footer: e.target.value })}
                  placeholder="e.g. Reply STOP to unsubscribe"
                />
              </div>

              {bodyVariables.length > 0 && (
                <div className="space-y-1.5">
                  <Label>Example values (required by Meta for submission)</Label>
                  <div className="space-y-1.5">
                    {bodyVariables.map((v, i) => (
                      <div key={v} className="flex items-center gap-2">
                        <span className="w-10 shrink-0 font-mono text-xs text-muted-foreground">{"{{"}{v}{"}}"}</span>
                        <Input
                          value={form.examples[i] || ""}
                          onChange={(e) => updateExample(i, e.target.value)}
                          placeholder={`Example for {{${v}}}`}
                        />
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <Label>Buttons (optional)</Label>
                  <Button variant="outline" size="sm" className="h-7 text-xs" onClick={addButton}>
                    <Plus className="mr-1 h-3 w-3" /> Add button
                  </Button>
                </div>
                {form.buttons.map((b, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <Select value={b.type} onValueChange={(v) => updateButton(i, { type: v })}>
                      <SelectTrigger className="w-36"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="QUICK_REPLY">Quick reply</SelectItem>
                        <SelectItem value="URL">URL</SelectItem>
                        <SelectItem value="PHONE_NUMBER">Phone</SelectItem>
                      </SelectContent>
                    </Select>
                    <Input
                      value={b.text}
                      onChange={(e) => updateButton(i, { text: e.target.value })}
                      placeholder="Button text"
                      className="flex-1"
                    />
                    {b.type === "URL" && (
                      <Input
                        value={b.url || ""}
                        onChange={(e) => updateButton(i, { url: e.target.value })}
                        placeholder="https://…"
                        className="flex-1"
                      />
                    )}
                    {b.type === "PHONE_NUMBER" && (
                      <Input
                        value={b.phone_number || ""}
                        onChange={(e) => updateButton(i, { phone_number: e.target.value })}
                        placeholder="+1…"
                        className="flex-1"
                      />
                    )}
                    <Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={() => removeButton(i)}>
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                ))}
              </div>
            </div>

            {/* Live WhatsApp-style preview */}
            <div className="space-y-1.5">
              <Label>Live preview</Label>
              <div className="rounded-xl border border-border bg-[#e5ddd5] p-4 dark:bg-[#0b141a]">
                <div className="mx-auto max-w-xs rounded-lg bg-white p-3 text-sm text-[#111b21] shadow dark:bg-[#202c33] dark:text-[#e9edef]">
                  {form.header_type === "TEXT" && form.header_text && (
                    <div className="mb-1.5 font-semibold">
                      {renderWithExamples(form.header_text, bodyVariables, form.examples)}
                    </div>
                  )}
                  {form.header_type !== "NONE" && form.header_type !== "TEXT" && (
                    <div className="mb-1.5 flex h-24 items-center justify-center rounded bg-secondary text-[10px] uppercase text-muted-foreground">
                      {form.header_type} placeholder
                    </div>
                  )}
                  <div className="whitespace-pre-wrap leading-relaxed">
                    {renderWithExamples(form.body, bodyVariables, form.examples) || (
                      <span className="text-muted-foreground">Body preview appears here…</span>
                    )}
                  </div>
                  {form.footer && (
                    <div className="mt-1.5 text-xs text-muted-foreground">
                      {renderWithExamples(form.footer, bodyVariables, form.examples)}
                    </div>
                  )}
                  {form.buttons.filter((b) => b.text?.trim()).length > 0 && (
                    <div className="mt-2 space-y-1 border-t border-border pt-2">
                      {form.buttons.filter((b) => b.text?.trim()).map((b, i) => (
                        <div
                          key={i}
                          className="flex items-center justify-center gap-1.5 rounded border border-border/60 py-1.5 text-xs font-medium text-primary"
                        >
                          <MessageCircle className="h-3 w-3" /> {b.text}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setFormOpen(false)}>Cancel</Button>
            <Button onClick={handleSave} disabled={saving} data-testid="wa-save-draft">
              {saving ? "Submitting…" : "Create & Submit to Meta"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function TemplateRow({ template, onSubmit, submitting }) {
  const [showPreview, setShowPreview] = useState(false);
  const tone = STATUS_TONE[template.status] || "neutral";

  return (
    <Card className="rounded-xl border-border bg-card p-4 shadow-sm" data-testid={`wa-template-${template.id}`}>
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <h3 className="truncate text-sm font-bold">{template.template_name}</h3>
          <div className="mt-0.5 flex flex-wrap items-center gap-1.5 text-[10px] uppercase tracking-wider text-muted-foreground">
            <span>{template.category || "—"}</span>
            <span>·</span>
            <span>{template.language}</span>
            <span>·</span>
            <span>v{template.version}</span>
          </div>
        </div>
        <StatusBadge status={template.status} tone={tone} />
      </div>

      <div className="mt-3 grid grid-cols-2 gap-x-3 gap-y-1 text-xs">
        <Row label="Meta template ID" value={template.provider_template_id || "—"} mono />
        <Row label="Quality rating" value={template.quality_rating || "—"} />
        <Row
          label="Last synced"
          value={template.last_synced_at ? new Date(template.last_synced_at).toLocaleString() : "never"}
        />
        <Row label="Variables" value={template.variables?.length ? template.variables.join(", ") : "none"} />
      </div>

      {template.rejection_reason && (
        <div className="mt-2 rounded-lg border border-rose-500/20 bg-rose-500/10 p-2 text-xs text-rose-700 dark:text-rose-400">
          Rejected: {template.rejection_reason}
        </div>
      )}

      {template.buttons?.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {template.buttons.map((b, i) => (
            <Badge key={i} variant="secondary" className="text-[10px] font-medium">{b.text}</Badge>
          ))}
        </div>
      )}

      <div className="mt-3 flex items-center gap-1.5">
        <Button variant="outline" size="sm" className="h-7 text-xs" onClick={() => setShowPreview((s) => !s)}>
          {showPreview ? "Hide preview" : "Preview"}
        </Button>
        {template.status === "DRAFT" && (
          <Button
            size="sm"
            className="h-7 text-xs"
            onClick={() => onSubmit(template)}
            disabled={submitting}
            data-testid={`wa-submit-${template.id}`}
          >
            <Send className="mr-1 h-3 w-3" /> {submitting ? "Submitting…" : "Submit to Meta"}
          </Button>
        )}
      </div>

      {showPreview && (
        <div className="mt-3 rounded-lg border border-border bg-secondary/30 p-3 text-xs leading-relaxed">
          {template.header_type === "TEXT" && template.header_text && (
            <div className="mb-1 font-semibold">{template.header_text}</div>
          )}
          <div className="whitespace-pre-wrap">{template.body}</div>
          {template.footer && <div className="mt-1 text-muted-foreground">{template.footer}</div>}
        </div>
      )}
    </Card>
  );
}

function Row({ label, value, mono }) {
  return (
    <div className="truncate">
      <span className="text-muted-foreground">{label}: </span>
      <span className={cn("font-medium", mono && "font-mono")}>{value}</span>
    </div>
  );
}

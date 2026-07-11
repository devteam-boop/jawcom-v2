import PageHeader from "@/components/PageHeader";
import StatusBadge from "@/components/StatusBadge";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
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
import { useTemplates } from "@/modules/templates";
import { templateService } from "@/services/templates";
import { useMemo, useState } from "react";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import {
  Plus,
  Copy,
  Archive,
  Trash2,
  Pencil,
  Search,
  FileText,
  Mail,
  MessageCircle,
  MessageSquare,
  Bell,
  CheckCircle2,
} from "lucide-react";

const CHANNELS = [
  { key: "whatsapp", label: "WhatsApp", icon: MessageCircle },
  { key: "email", label: "Email", icon: Mail },
  { key: "sms", label: "SMS", icon: MessageSquare },
  { key: "push", label: "Push", icon: Bell },
];

const STATUS_META = {
  draft: { badge: "Draft", tone: "neutral" },
  active: { badge: "Active", tone: "success" },
  inactive: { badge: "Archived", tone: "danger" },
};

const STATUS_FILTERS = [
  { key: "all", label: "All" },
  { key: "draft", label: "Draft" },
  { key: "active", label: "Active" },
  { key: "inactive", label: "Archived" },
];

function extractVars(content = "") {
  const set = new Set();
  const re = /\{\{(\w+)\}\}/g;
  let m;
  while ((m = re.exec(content)) !== null) set.add(m[1]);
  return Array.from(set);
}

function previewContent(content) {
  if (!content) return content;
  return content.replace(/\{\{(\w+)\}\}/g, (match, name) => `«${name}»`);
}

const EMPTY_FORM = { name: "", channel: "whatsapp", subject: "", content: "" };

export default function Templates() {
  const [folder, setFolder] = useState("whatsapp");
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const { templates, loading, refetch } = useTemplates(folder);
  const [selectedId, setSelectedId] = useState(null);

  const [formOpen, setFormOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);

  const filtered = useMemo(
    () =>
      templates.filter((t) => {
        if (statusFilter !== "all" && t.status !== statusFilter) return false;
        return !query || `${t.name} ${t.content}`.toLowerCase().includes(query.toLowerCase());
      }),
    [templates, query, statusFilter]
  );
  const selected = filtered.find((t) => t.id === selectedId) || filtered[0] || null;
  const activeChannel = CHANNELS.find((f) => f.key === folder);

  const openCreate = () => {
    setEditingId(null);
    setForm({ ...EMPTY_FORM, channel: folder });
    setFormOpen(true);
  };

  const openEdit = (template) => {
    setEditingId(template.id);
    setForm({
      name: template.name,
      channel: template.channel,
      subject: template.subject || "",
      content: template.content,
    });
    setFormOpen(true);
  };

  const handleSave = async () => {
    if (!form.name.trim() || !form.content.trim()) {
      toast.error("Name and content are required");
      return;
    }
    setSaving(true);
    try {
      const payload = {
        name: form.name.trim(),
        channel: form.channel,
        subject: form.channel === "email" ? form.subject : null,
        content: form.content,
      };
      if (editingId) {
        await templateService.update(editingId, payload);
        toast.success("Template updated");
      } else {
        await templateService.create(payload);
        toast.success("Template created");
      }
      setFormOpen(false);
      await refetch();
    } catch (err) {
      toast.error(err.message || "Failed to save template");
    } finally {
      setSaving(false);
    }
  };

  const handleDuplicate = async (template) => {
    try {
      await templateService.duplicate(template.id);
      toast.success("Template duplicated");
      await refetch();
    } catch (err) {
      toast.error(err.message || "Failed to duplicate template");
    }
  };

  const handleArchive = async (template) => {
    try {
      await templateService.archive(template.id);
      toast.success("Template archived");
      await refetch();
    } catch (err) {
      toast.error(err.message || "Failed to archive template");
    }
  };

  const handleActivate = async (template) => {
    try {
      await templateService.activate(template.id);
      toast.success("Template activated");
      await refetch();
    } catch (err) {
      toast.error(err?.body?.detail || err.message || "Failed to activate template");
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await templateService.delete(deleteTarget.id);
      toast.success("Template deleted");
      setDeleteTarget(null);
      setSelectedId(null);
      await refetch();
    } catch (err) {
      toast.error(err?.body?.detail || err.message || "Failed to delete template");
    }
  };

  return (
    <div data-testid="page-templates" className="flex h-full min-h-0 flex-col">
      <PageHeader
        title="Template Library"
        description="Reusable, approved messages for every channel."
        actions={
          <Button size="sm" onClick={openCreate} data-testid="template-new">
            <Plus className="mr-2 h-3.5 w-3.5" /> New template
          </Button>
        }
      />

      <div className="grid min-h-0 flex-1 grid-cols-1 lg:grid-cols-[220px_1fr_320px]">
        {/* Left: channel folders */}
        <aside className="overflow-y-auto scrollbar-thin border-r border-border bg-card/40 p-3" data-testid="template-folders">
          <div className="mb-2 px-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Channels</div>
          <div className="space-y-1">
            {CHANNELS.map((f) => {
              const Icon = f.icon;
              const isActive = f.key === folder;
              return (
                <button
                  key={f.key}
                  onClick={() => { setFolder(f.key); setSelectedId(null); }}
                  className={cn(
                    "flex w-full items-center gap-2 rounded-lg px-2.5 py-1.5 text-left text-sm",
                    isActive ? "bg-accent text-accent-foreground" : "text-muted-foreground hover:bg-secondary hover:text-foreground"
                  )}
                  data-testid={`folder-${f.key}`}
                >
                  <Icon className="h-3.5 w-3.5" />
                  <span className="flex-1 text-xs font-semibold">{f.label}</span>
                </button>
              );
            })}
          </div>
        </aside>

        {/* Center: template list */}
        <main className="overflow-y-auto scrollbar-thin p-4 md:p-6" data-testid="template-list">
          <div className="mb-3 flex items-center gap-2">
            <div className="relative flex-1 max-w-sm">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search templates…" className="h-9 pl-9" data-testid="template-search" />
            </div>
            <span className="text-xs text-muted-foreground">{filtered.length} in {activeChannel?.label}</span>
          </div>

          <Tabs value={statusFilter} onValueChange={setStatusFilter} className="mb-3">
            <TabsList data-testid="template-status-filter">
              {STATUS_FILTERS.map((f) => (
                <TabsTrigger key={f.key} value={f.key} className="text-xs" data-testid={`status-filter-${f.key}`}>
                  {f.label}
                </TabsTrigger>
              ))}
            </TabsList>
          </Tabs>

          {loading ? (
            <div className="flex items-center justify-center p-12 text-sm text-muted-foreground">Loading…</div>
          ) : filtered.length === 0 ? (
            <div className="rounded-xl border border-dashed border-border p-8 text-center text-sm text-muted-foreground">
              No templates yet for {activeChannel?.label}. Create one to get started.
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              {filtered.map((t) => {
                const isSel = t.id === selected?.id;
                const meta = STATUS_META[t.status] || STATUS_META.draft;
                const variables = extractVars(t.content);
                return (
                  <Card
                    key={t.id}
                    onClick={() => setSelectedId(t.id)}
                    className={cn(
                      "cursor-pointer rounded-xl border-border bg-card p-4 shadow-sm transition-colors",
                      isSel ? "border-primary ring-2 ring-primary/15" : "hover:border-primary/30"
                    )}
                    data-testid={`template-card-${t.id}`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <span className="inline-flex rounded-md bg-secondary px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                        {t.channel}
                      </span>
                      <StatusBadge status={meta.badge} tone={meta.tone} />
                    </div>
                    <h3 className="mt-2 truncate text-sm font-bold">{t.name}</h3>
                    <div className="mt-3 rounded-lg border border-border bg-secondary/40 p-2.5 font-mono text-[11px] leading-relaxed text-muted-foreground">
                      <div className="line-clamp-2">{t.content}</div>
                    </div>
                    {variables.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {variables.map((v) => (
                          <span key={v} className="rounded bg-primary/10 px-1.5 py-0.5 font-mono text-[10px] font-semibold text-primary">{"{{"}{v}{"}}"}</span>
                        ))}
                      </div>
                    )}
                  </Card>
                );
              })}
            </div>
          )}
        </main>

        {/* Right: preview */}
        <aside className="overflow-y-auto scrollbar-thin border-l border-border bg-card/40 p-5" data-testid="template-preview">
          {selected ? (
            <>
              <div className="mb-3 flex items-center justify-between">
                <h3 className="text-sm font-bold">Preview</h3>
                <StatusBadge status={(STATUS_META[selected.status] || STATUS_META.draft).badge} tone={(STATUS_META[selected.status] || STATUS_META.draft).tone} />
              </div>

              <Card className="rounded-lg border-border bg-background p-3">
                <div className="text-[10px] uppercase tracking-wider text-muted-foreground">{selected.channel}</div>
                <div className="mt-1 text-sm font-semibold">{selected.name}</div>
                {selected.subject && (
                  <div className="mt-1 text-xs text-muted-foreground">Subject: {previewContent(selected.subject)}</div>
                )}
                <div className="mt-3 rounded-lg border border-border bg-secondary/30 p-3 font-mono text-xs leading-relaxed">
                  {previewContent(selected.content).split("\n").map((line, i) => <div key={i}>{line}</div>)}
                </div>
              </Card>

              <Tabs defaultValue="vars" className="mt-4">
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="vars" className="text-xs">Variables</TabsTrigger>
                  <TabsTrigger value="meta" className="text-xs">Metadata</TabsTrigger>
                </TabsList>
                <TabsContent value="vars" className="mt-3 space-y-2">
                  {extractVars(selected.content).length === 0 ? (
                    <div className="rounded-lg border border-dashed border-border p-3 text-center text-xs text-muted-foreground">
                      No variables in this template
                    </div>
                  ) : (
                    extractVars(selected.content).map((v) => (
                      <div key={v} className="flex items-center justify-between rounded-lg border border-border p-2.5">
                        <span className="font-mono text-xs font-semibold">{"{{"}{v}{"}}"}</span>
                        <span className="font-mono text-xs text-muted-foreground">«{v}»</span>
                      </div>
                    ))
                  )}
                </TabsContent>
                <TabsContent value="meta" className="mt-3 space-y-2">
                  <Row label="Channel" value={selected.channel} />
                  <Row label="Status" value={(STATUS_META[selected.status] || STATUS_META.draft).badge} />
                  <Row label="Created" value={selected.created_at ? new Date(selected.created_at).toLocaleString() : "—"} />
                  <Row label="Updated" value={selected.updated_at ? new Date(selected.updated_at).toLocaleString() : "—"} />
                </TabsContent>
              </Tabs>

              <div className="mt-5 space-y-1.5">
                <div className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Actions</div>
                <div className="grid grid-cols-2 gap-1.5">
                  {selected.channel === "email" && (
                    <Button
                      variant="outline"
                      size="sm"
                      className="h-8 text-xs"
                      disabled={selected.status === "active"}
                      onClick={() => handleActivate(selected)}
                      data-testid="tpl-activate"
                    >
                      <CheckCircle2 className="mr-1 h-3 w-3" /> Activate
                    </Button>
                  )}
                  <Button variant="outline" size="sm" className="h-8 text-xs" onClick={() => openEdit(selected)} data-testid="tpl-edit">
                    <Pencil className="mr-1 h-3 w-3" /> Edit
                  </Button>
                  <Button variant="outline" size="sm" className="h-8 text-xs" onClick={() => handleDuplicate(selected)} data-testid="tpl-duplicate">
                    <Copy className="mr-1 h-3 w-3" /> Duplicate
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-8 text-xs"
                    disabled={selected.status === "inactive"}
                    onClick={() => handleArchive(selected)}
                    data-testid="tpl-archive"
                  >
                    <Archive className="mr-1 h-3 w-3" /> Archive
                  </Button>
                  <Button variant="destructive" size="sm" className="h-8 text-xs" onClick={() => setDeleteTarget(selected)} data-testid="tpl-delete">
                    <Trash2 className="mr-1 h-3 w-3" /> Delete
                  </Button>
                </div>
              </div>
            </>
          ) : (
            <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
              <FileText className="mr-2 h-4 w-4" /> Pick a template to preview
            </div>
          )}
        </aside>
      </div>

      {/* Create / Edit dialog */}
      <Dialog open={formOpen} onOpenChange={setFormOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingId ? "Edit Template" : "New Template"}</DialogTitle>
            <DialogDescription>
              Use <code>{"{{variable}}"}</code> placeholders — they resolve from lead/company data at send time.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label>Name</Label>
                <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="e.g. Welcome message" />
              </div>
              <div className="space-y-1.5">
                <Label>Channel</Label>
                <Select value={form.channel} onValueChange={(v) => setForm({ ...form, channel: v })} disabled={!!editingId}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {CHANNELS.map((c) => (
                      <SelectItem key={c.key} value={c.key}>{c.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            {form.channel === "email" && (
              <div className="space-y-1.5">
                <Label>Subject</Label>
                <Input value={form.subject} onChange={(e) => setForm({ ...form, subject: e.target.value })} placeholder="e.g. Welcome to {{company.name}}" />
              </div>
            )}
            <div className="space-y-1.5">
              <Label>Content</Label>
              <Textarea
                value={form.content}
                onChange={(e) => setForm({ ...form, content: e.target.value })}
                placeholder="e.g. Hi {{lead.name}}, welcome aboard!"
                rows={6}
                className="font-mono text-xs"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setFormOpen(false)}>Cancel</Button>
            <Button onClick={handleSave} disabled={saving}>{editingId ? "Save changes" : "Create"}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete confirmation */}
      <Dialog open={!!deleteTarget} onOpenChange={(open) => !open && setDeleteTarget(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Template</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{deleteTarget?.name}"? This cannot be undone. Templates still
              referenced by a stage mapping or a flow node cannot be deleted.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteTarget(null)}>Cancel</Button>
            <Button variant="destructive" onClick={handleDelete}>Delete</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function Row({ label, value }) {
  return (
    <div className="flex items-center justify-between border-b border-border/60 pb-2 text-sm">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className="text-sm font-medium">{value}</span>
    </div>
  );
}

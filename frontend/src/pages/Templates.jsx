import PageHeader from "@/components/PageHeader";
import StatusBadge from "@/components/StatusBadge";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { TEMPLATES } from "@/dummy-data/templates";
import { useMemo, useState } from "react";
import { cn } from "@/lib/utils";
import {
  Plus,
  Copy,
  Archive,
  Play,
  CheckCircle2,
  XCircle,
  Search,
  FileText,
  Mail,
  MessageCircle,
  Instagram,
  Phone,
  Facebook,
  MessageSquare,
} from "lucide-react";

const FOLDERS = [
  { key: "whatsapp", label: "WhatsApp", icon: MessageCircle, source: TEMPLATES.whatsapp, channel: "WhatsApp" },
  { key: "email", label: "Email", icon: Mail, source: TEMPLATES.email, channel: "Email" },
  { key: "sms", label: "SMS", icon: MessageSquare, source: TEMPLATES.sms, channel: "SMS" },
  { key: "instagram", label: "Instagram", icon: Instagram, source: [
    { id: "ti1", name: "IG welcome DM", preview: "Hey {{first_name}} — thanks for the follow! Here's a peek at what we do.", language: "EN", category: "Marketing", status: "Approved", lastEdited: "Feb 4", version: "v1.3" },
    { id: "ti2", name: "Product tag reply", preview: "Great pick, {{first_name}}! Tap the link in bio to grab yours.", language: "EN", category: "Utility", status: "In Review", lastEdited: "Today", version: "v0.2" },
  ], channel: "Instagram" },
  { key: "messenger", label: "Messenger", icon: Facebook, source: [
    { id: "tm1", name: "Support handoff", preview: "Hi {{first_name}}, connecting you with a specialist now.", language: "EN", category: "Support", status: "Approved", lastEdited: "Jan 18", version: "v2.0" },
    { id: "tm2", name: "Offer nudge", preview: "Still deciding, {{first_name}}? Here's a 10% loyalty code: {{code}}.", language: "EN", category: "Marketing", status: "Draft", lastEdited: "Today", version: "v0.1" },
  ], channel: "Messenger" },
  { key: "voice", label: "Voice", icon: Phone, source: TEMPLATES.voice, channel: "Voice" },
];

const STATUS_META = {
  Approved: { badge: "Active", tone: "success" },
  "In Review": { badge: "Open", tone: "info" },
  Pending: { badge: "Open", tone: "info" },
  Draft: { badge: "Draft", tone: "neutral" },
  Rejected: { badge: "Lost", tone: "danger" },
  Archived: { badge: "Closed", tone: "neutral" },
};

function normalize(t) {
  return {
    ...t,
    version: t.version || "v1.0",
    updatedBy: "Maya Iyer",
    variables: extractVars(t.preview),
  };
}

function extractVars(text = "") {
  const set = new Set();
  const re = /\{\{(\w+)\}\}/g;
  let m;
  while ((m = re.exec(text)) !== null) set.add(m[1]);
  return Array.from(set);
}

export default function Templates() {
  const [folder, setFolder] = useState("whatsapp");
  const [query, setQuery] = useState("");
  const active = FOLDERS.find((f) => f.key === folder);
  const templates = useMemo(() => (active?.source || []).map(normalize), [active]);
  const filtered = useMemo(
    () => templates.filter((t) => !query || `${t.name} ${t.preview}`.toLowerCase().includes(query.toLowerCase())),
    [templates, query]
  );
  const [selectedId, setSelectedId] = useState(filtered[0]?.id);
  const selected = filtered.find((t) => t.id === selectedId) || filtered[0];

  return (
    <div data-testid="page-templates" className="flex h-full min-h-0 flex-col">
      <PageHeader
        title="Template Library"
        description="Reusable, approved messages for every channel."
        actions={
          <Button size="sm" data-testid="template-new">
            <Plus className="mr-2 h-3.5 w-3.5" /> New template
          </Button>
        }
      />

      <div className="grid min-h-0 flex-1 grid-cols-1 lg:grid-cols-[220px_1fr_320px]">
        {/* Left: folders */}
        <aside className="overflow-y-auto scrollbar-thin border-r border-border bg-card/40 p-3" data-testid="template-folders">
          <div className="mb-2 px-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Folders</div>
          <div className="space-y-1">
            {FOLDERS.map((f) => {
              const Icon = f.icon;
              const isActive = f.key === folder;
              const count = f.source.length;
              return (
                <button
                  key={f.key}
                  onClick={() => { setFolder(f.key); setSelectedId(f.source[0]?.id); }}
                  className={cn(
                    "flex w-full items-center gap-2 rounded-lg px-2.5 py-1.5 text-left text-sm",
                    isActive ? "bg-accent text-accent-foreground" : "text-muted-foreground hover:bg-secondary hover:text-foreground"
                  )}
                  data-testid={`folder-${f.key}`}
                >
                  <Icon className="h-3.5 w-3.5" />
                  <span className="flex-1 text-xs font-semibold">{f.label}</span>
                  <span className="rounded bg-secondary px-1.5 text-[10px] font-semibold text-muted-foreground">{count}</span>
                </button>
              );
            })}
          </div>

          <div className="mt-5 space-y-1">
            <div className="mb-1 px-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Status</div>
            {["Draft", "Pending", "Approved", "Rejected", "Archived"].map((s) => (
              <div key={s} className="flex items-center justify-between rounded-md px-2 py-1 text-xs text-muted-foreground">
                <span>{s}</span>
                <StatusBadge status={STATUS_META[s]?.badge || "Draft"} tone={STATUS_META[s]?.tone} />
              </div>
            ))}
          </div>
        </aside>

        {/* Center: template list */}
        <main className="overflow-y-auto scrollbar-thin p-4 md:p-6" data-testid="template-list">
          <div className="mb-3 flex items-center gap-2">
            <div className="relative flex-1 max-w-sm">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search templates…" className="h-9 pl-9" data-testid="template-search" />
            </div>
            <span className="text-xs text-muted-foreground">{filtered.length} in {active.label}</span>
          </div>

          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            {filtered.map((t) => {
              const isSel = t.id === selected?.id;
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
                      {t.category}
                    </span>
                    <StatusBadge status={STATUS_META[t.status]?.badge || "Draft"} tone={STATUS_META[t.status]?.tone} />
                  </div>
                  <h3 className="mt-2 truncate text-sm font-bold">{t.name}</h3>
                  <p className="mt-0.5 text-[11px] text-muted-foreground">{t.language} · {t.version} · Updated {t.lastEdited}</p>
                  <div className="mt-3 rounded-lg border border-border bg-secondary/40 p-2.5 font-mono text-[11px] leading-relaxed text-muted-foreground">
                    <div className="line-clamp-2">{t.preview.split("\n")[0]}</div>
                  </div>
                  {t.variables.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {t.variables.map((v) => (
                        <span key={v} className="rounded bg-primary/10 px-1.5 py-0.5 font-mono text-[10px] font-semibold text-primary">{"{{"}{v}{"}}"}</span>
                      ))}
                    </div>
                  )}
                </Card>
              );
            })}
          </div>
        </main>

        {/* Right: preview */}
        <aside className="overflow-y-auto scrollbar-thin border-l border-border bg-card/40 p-5" data-testid="template-preview">
          {selected ? (
            <>
              <div className="mb-3 flex items-center justify-between">
                <h3 className="text-sm font-bold">Preview</h3>
                <StatusBadge status={STATUS_META[selected.status]?.badge || "Draft"} tone={STATUS_META[selected.status]?.tone} />
              </div>

              <Card className="rounded-lg border-border bg-background p-3">
                <div className="text-[10px] uppercase tracking-wider text-muted-foreground">{active.channel} · {selected.language}</div>
                <div className="mt-1 text-sm font-semibold">{selected.name}</div>
                <div className="mt-3 rounded-lg border border-border bg-secondary/30 p-3 font-mono text-xs leading-relaxed">
                  {selected.preview.split("\n").map((line, i) => <div key={i}>{line}</div>)}
                </div>
              </Card>

              <Tabs defaultValue="vars" className="mt-4">
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="vars" className="text-xs">Variables</TabsTrigger>
                  <TabsTrigger value="meta" className="text-xs">Metadata</TabsTrigger>
                </TabsList>
                <TabsContent value="vars" className="mt-3 space-y-2">
                  {selected.variables.length === 0 ? (
                    <div className="rounded-lg border border-dashed border-border p-3 text-center text-xs text-muted-foreground">
                      No variables in this template
                    </div>
                  ) : (
                    selected.variables.map((v) => (
                      <div key={v} className="flex items-center justify-between rounded-lg border border-border p-2.5">
                        <span className="font-mono text-xs font-semibold">{"{{"}{v}{"}}"}</span>
                        <Input defaultValue={
                          v === "first_name" ? "Priya" :
                          v === "code" ? "SAVE10" :
                          v === "date" ? "Feb 20" :
                          v === "time" ? "3:00 PM" :
                          v === "owner" ? "Maya" :
                          v === "plan" ? "Growth" :
                          v === "product" ? "Analytics" :
                          v === "order_id" ? "JAW-4821" :
                          v === "link" ? "jaw.co/x9" :
                          v === "days" ? "7" :
                          v === "workspace" ? "JawCom" :
                          v === "year" ? "2026" :
                          "sample"
                        } className="h-7 max-w-[140px] font-mono text-xs" />
                      </div>
                    ))
                  )}
                </TabsContent>
                <TabsContent value="meta" className="mt-3 space-y-2">
                  <Row label="Approval status" value={<StatusBadge status={STATUS_META[selected.status]?.badge || "Draft"} tone={STATUS_META[selected.status]?.tone} />} />
                  <Row label="Version" value={selected.version} />
                  <Row label="Language" value={selected.language} />
                  <Row label="Category" value={selected.category} />
                  <Row label="Last updated" value={selected.lastEdited} />
                  <Row label="Updated by" value={selected.updatedBy} />
                </TabsContent>
              </Tabs>

              <div className="mt-5 space-y-1.5">
                <div className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Actions</div>
                <div className="grid grid-cols-2 gap-1.5">
                  <Button variant="outline" size="sm" className="h-8 text-xs" data-testid="tpl-duplicate">
                    <Copy className="mr-1 h-3 w-3" /> Duplicate
                  </Button>
                  <Button variant="outline" size="sm" className="h-8 text-xs" data-testid="tpl-archive">
                    <Archive className="mr-1 h-3 w-3" /> Archive
                  </Button>
                  <Button variant="outline" size="sm" className="h-8 text-xs" data-testid="tpl-test">
                    <Play className="mr-1 h-3 w-3" /> Test
                  </Button>
                  <Button variant="outline" size="sm" className="h-8 text-xs" data-testid="tpl-reject">
                    <XCircle className="mr-1 h-3 w-3" /> Reject
                  </Button>
                  <Button size="sm" className="col-span-2 h-8 text-xs" data-testid="tpl-approve">
                    <CheckCircle2 className="mr-1 h-3 w-3" /> Approve
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

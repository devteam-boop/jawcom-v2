import { useMemo, useState } from "react";
import PageHeader from "@/components/PageHeader";
import SearchBar from "@/components/SearchBar";
import StatusBadge from "@/components/StatusBadge";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { KNOWLEDGE_DOCS } from "@/dummy-data/knowledge";
import {
  BookOpen,
  Globe,
  FileText,
  HelpCircle,
  DollarSign,
  ShieldCheck,
  Megaphone,
  HardDrive,
  Plus,
  CheckCircle2,
  Loader2,
  XCircle,
  RefreshCw,
  Upload,
  Sparkles,
  MessageSquare,
  BookMarked,
  Speech,
  Brain,
} from "lucide-react";

const CATEGORIES = [
  { key: "all", label: "All", icon: BookOpen },
  { key: "docs", label: "Documents", icon: FileText },
  { key: "faqs", label: "FAQs", icon: HelpCircle },
  { key: "scripts", label: "Sales Scripts", icon: Speech },
  { key: "pricing", label: "Pricing", icon: DollarSign },
  { key: "policies", label: "Policies", icon: ShieldCheck },
  { key: "objections", label: "Objection Handling", icon: MessageSquare },
  { key: "pdfs", label: "Uploaded PDFs", icon: FileText },
  { key: "web", label: "Website Links", icon: Globe },
  { key: "training", label: "Training Material", icon: BookMarked },
  { key: "memory", label: "Conversation Memory", icon: Brain },
];

const EXTRA_KNOWLEDGE = [
  { id: "sc1", title: "Discovery call script", type: "Sales Scripts", source: "Playbooks · v3", status: "Indexed", embedding: "Synced", aiReady: true, chunks: 42, updated: "Yesterday", size: "68 KB", category: "scripts" },
  { id: "sc2", title: "Objection: pricing", type: "Objection", source: "Playbooks · pricing.md", status: "Indexed", embedding: "Synced", aiReady: true, chunks: 18, updated: "3d ago", size: "42 KB", category: "objections" },
  { id: "sc3", title: "Objection: security", type: "Objection", source: "Playbooks · security.md", status: "Indexed", embedding: "Synced", aiReady: true, chunks: 22, updated: "6d ago", size: "58 KB", category: "objections" },
  { id: "sc4", title: "Objection: onboarding time", type: "Objection", source: "Playbooks · onboarding.md", status: "Indexed", embedding: "Synced", aiReady: true, chunks: 14, updated: "1w ago", size: "36 KB", category: "objections" },
  { id: "tr1", title: "New rep onboarding · Week 1", type: "Training", source: "Notion · CS wiki", status: "Indexed", embedding: "Synced", aiReady: true, chunks: 96, updated: "Feb 10", size: "1.2 MB", category: "training" },
  { id: "tr2", title: "Product 101 · Recorded talk", type: "Training", source: "Loom · 24m", status: "Embedding", embedding: "In progress", aiReady: false, chunks: 0, updated: "Just now", size: "184 MB", category: "training" },
  { id: "mem1", title: "Priya Sharma · Growth negotiation", type: "Memory", source: "Auto · from thread", status: "Indexed", embedding: "Synced", aiReady: true, chunks: 6, updated: "2h ago", size: "12 KB", category: "memory" },
  { id: "mem2", title: "Northwind · Procurement notes", type: "Memory", source: "Auto · from thread", status: "Indexed", embedding: "Synced", aiReady: true, chunks: 8, updated: "Yesterday", size: "18 KB", category: "memory" },
  { id: "faq1", title: "FAQ · Billing", type: "FAQ", source: "help.jawcom.io/billing", status: "Indexed", embedding: "Synced", aiReady: true, chunks: 41, updated: "6d ago", size: "120 KB", category: "faqs" },
  { id: "faq2", title: "FAQ · Integrations", type: "FAQ", source: "help.jawcom.io/integrations", status: "Indexed", embedding: "Synced", aiReady: true, chunks: 58, updated: "6d ago", size: "160 KB", category: "faqs" },
];

function mapExisting(d) {
  const map = {
    Website: "web",
    PDF: "pdfs",
    FAQ: "faqs",
    Pricing: "pricing",
    Policies: "policies",
    Brochure: "docs",
    Drive: "docs",
  };
  return { ...d, category: map[d.type] || "docs" };
}

const ALL_DOCS = [...KNOWLEDGE_DOCS.map(mapExisting), ...EXTRA_KNOWLEDGE];

const TYPE_ICON = {
  Website: Globe,
  PDF: FileText,
  FAQ: HelpCircle,
  Pricing: DollarSign,
  Policies: ShieldCheck,
  Brochure: Megaphone,
  Drive: HardDrive,
  "Sales Scripts": Speech,
  Objection: MessageSquare,
  Training: BookMarked,
  Memory: Brain,
};

const EMBEDDING_META = {
  Synced: { icon: CheckCircle2, color: "text-emerald-500" },
  "In progress": { icon: Loader2, color: "text-amber-500 animate-spin" },
  Error: { icon: XCircle, color: "text-rose-500" },
};

export default function Knowledge() {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("all");

  const docs = useMemo(() => {
    return ALL_DOCS.filter((d) => {
      if (category !== "all" && d.category !== category) return false;
      if (search && !`${d.title} ${d.source} ${d.type}`.toLowerCase().includes(search.toLowerCase())) return false;
      return true;
    });
  }, [search, category]);

  const totalChunks = ALL_DOCS.reduce((acc, d) => acc + d.chunks, 0);
  const ready = ALL_DOCS.filter((d) => d.aiReady).length;

  return (
    <div data-testid="page-knowledge">
      <PageHeader
        title="AI Knowledge Center"
        description="Everything your assistant references when replying to customers."
        actions={
          <>
            <Button variant="outline" size="sm" data-testid="knowledge-reindex">
              <RefreshCw className="mr-2 h-3.5 w-3.5" /> Reindex
            </Button>
            <Button size="sm" data-testid="knowledge-upload">
              <Upload className="mr-2 h-3.5 w-3.5" /> Upload
            </Button>
            <Button variant="outline" size="sm" data-testid="knowledge-add">
              <Plus className="mr-2 h-3.5 w-3.5" /> Add source
            </Button>
          </>
        }
      />

      <div className="space-y-5 px-4 py-6 md:px-8">
        {/* Summary */}
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <SummaryCard label="Sources" value={ALL_DOCS.length} icon={BookOpen} />
          <SummaryCard label="AI-ready" value={`${ready} / ${ALL_DOCS.length}`} icon={Sparkles} />
          <SummaryCard label="Chunks" value={totalChunks.toLocaleString()} icon={FileText} />
          <SummaryCard label="Storage" value="192 MB" icon={HardDrive} />
        </div>

        {/* Search + categories */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <SearchBar value={search} onChange={setSearch} placeholder="Search sources, FAQs, scripts, memory…" className="w-full sm:max-w-sm" testId="knowledge-search" />
        </div>

        <div className="flex flex-wrap items-center gap-1.5" data-testid="knowledge-categories">
          {CATEGORIES.map((c) => {
            const Icon = c.icon;
            const active = c.key === category;
            const count = c.key === "all" ? ALL_DOCS.length : ALL_DOCS.filter((d) => d.category === c.key).length;
            return (
              <button
                key={c.key}
                onClick={() => setCategory(c.key)}
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium transition-colors",
                  active ? "border-primary bg-primary/10 text-primary" : "border-border text-muted-foreground hover:text-foreground"
                )}
                data-testid={`knowledge-cat-${c.key}`}
              >
                <Icon className="h-3 w-3" />
                {c.label}
                <span className={cn("rounded px-1 text-[10px] font-semibold", active ? "bg-primary/10" : "bg-secondary")}>{count}</span>
              </button>
            );
          })}
        </div>

        {/* Doc grid */}
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {docs.map((d) => {
            const TypeIcon = TYPE_ICON[d.type] || FileText;
            const emb = EMBEDDING_META[d.embedding] || EMBEDDING_META.Synced;
            const EmbIcon = emb.icon;
            return (
              <Card
                key={d.id}
                className="rounded-xl border-border bg-card p-5 shadow-sm transition-colors hover:border-primary/30"
                data-testid={`doc-${d.id}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex h-11 w-11 items-center justify-center rounded-lg border border-border bg-secondary/60">
                    <TypeIcon className="h-5 w-5" />
                  </div>
                  {d.aiReady ? (
                    <Badge variant="outline" className="border-primary/20 bg-primary/10 text-[10px] font-semibold text-primary">
                      AI Ready
                    </Badge>
                  ) : (
                    <Badge variant="outline" className="text-[10px]">Not ready</Badge>
                  )}
                </div>

                <h3 className="mt-4 truncate text-base font-bold">{d.title}</h3>
                <p className="mt-0.5 truncate text-xs text-muted-foreground">{d.type} · {d.source}</p>

                <div className="mt-4 grid grid-cols-3 gap-2 border-t border-border pt-4 text-xs">
                  <div>
                    <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Status</div>
                    <div className="mt-0.5">
                      <StatusBadge status={d.status === "Indexed" ? "Active" : d.status === "Embedding" ? "Open" : "Lost"} tone={d.status === "Failed" ? "danger" : undefined} />
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Embedding</div>
                    <div className="mt-1 flex items-center gap-1 text-[11px] font-medium">
                      <EmbIcon className={cn("h-3 w-3", emb.color)} />
                      <span>{d.embedding}</span>
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Chunks</div>
                    <div className="mt-0.5 font-mono text-sm font-semibold">{d.chunks}</div>
                  </div>
                </div>

                <div className="mt-3 flex items-center justify-between text-[11px] text-muted-foreground">
                  <span>Updated {d.updated}</span>
                  <span>{d.size}</span>
                </div>
              </Card>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function SummaryCard({ label, value, icon: Icon }) {
  return (
    <Card className="rounded-xl border-border bg-card p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-muted-foreground">{label}</span>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </div>
      <div className="mt-2 font-mono text-2xl font-semibold">{value}</div>
    </Card>
  );
}

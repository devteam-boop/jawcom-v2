import { useMemo } from "react";
import StatusBadge from "@/components/StatusBadge";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { Search, FileText } from "lucide-react";

const STATUS_META = {
  Approved: { badge: "Active", tone: "success" },
  "In Review": { badge: "Open", tone: "info" },
  Pending: { badge: "Open", tone: "info" },
  Draft: { badge: "Draft", tone: "neutral" },
  Rejected: { badge: "Lost", tone: "danger" },
  Archived: { badge: "Closed", tone: "neutral" },
};

export default function TemplateList({ templates, selectedId, onSelect, search, onSearchChange }) {
  const filtered = useMemo(() => {
    return templates.filter((t) => !search || `${t.name} ${t.preview}`.toLowerCase().includes(search.toLowerCase()));
  }, [templates, search]);

  return (
    <main className="overflow-y-auto scrollbar-thin p-4 md:p-6">
      <div className="mb-3 flex items-center gap-2">
        <div className="relative flex-1 max-w-sm">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input value={search} onChange={(e) => onSearchChange(e.target.value)} placeholder="Search templates…" className="h-9 pl-9" />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        {filtered.map((t) => {
          const isSel = t.id === selectedId;
          const meta = STATUS_META[t.status] || STATUS_META.Draft;
          return (
            <Card
              key={t.id}
              onClick={() => onSelect(t.id)}
              className={cn("cursor-pointer rounded-xl border-border bg-card p-4 shadow-sm transition-colors", isSel ? "border-primary ring-2 ring-primary/15" : "hover:border-primary/30")}
            >
              <div className="flex items-start justify-between gap-2">
                <span className="inline-flex rounded-md bg-secondary px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                  {t.category}
                </span>
                <StatusBadge status={meta.badge} tone={meta.tone} />
              </div>
              <h3 className="mt-2 truncate text-sm font-bold">{t.name}</h3>
              <div className="mt-2 rounded-lg border border-border bg-secondary/40 p-2.5 font-mono text-[11px] leading-relaxed text-muted-foreground">
                <div className="line-clamp-2">{t.preview}</div>
              </div>
            </Card>
          );
        })}
      </div>
    </main>
  );
}

import { useMemo } from "react";
import FilterBar from "@/components/FilterBar";
import StatusBadge from "@/components/StatusBadge";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Send, Eye, CheckCircle2, Reply, Users, Calendar, FileText } from "lucide-react";

const FILTERS = [
  { label: "All", value: "all" },
  { label: "Draft", value: "Draft" },
  { label: "Scheduled", value: "Scheduled" },
  { label: "Running", value: "Running" },
  { label: "Completed", value: "Completed" },
];

const channelColor = {
  WhatsApp: "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400",
  Email: "bg-blue-500/10 text-blue-700 dark:text-blue-400",
  SMS: "bg-amber-500/10 text-amber-700 dark:text-amber-400",
};

function Metric({ icon: Icon, label, value }) {
  return (
    <div>
      <div className="flex items-center gap-1 text-[10px] uppercase tracking-wider text-muted-foreground">
        <Icon className="h-3 w-3" /> {label}
      </div>
      <div className="mt-0.5 font-mono text-sm font-semibold">{value}</div>
    </div>
  );
}

export default function CampaignList({ campaigns, filter, onFilterChange }) {
  const filterOptions = FILTERS.map((f) => ({
    ...f,
    count: f.value === "all" ? campaigns.length : campaigns.filter((c) => c.status === f.value).length,
  }));

  const rows = useMemo(() => {
    return campaigns.filter((c) => filter === "all" || c.status === filter);
  }, [campaigns, filter]);

  return (
    <div className="space-y-5">
      <FilterBar options={filterOptions} value={filter} onChange={onFilterChange} testId="campaigns-filter" />

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {rows.map((c) => (
          <Card key={c.id} className="rounded-xl border-border bg-card p-5 shadow-sm transition-colors hover:border-primary/30">
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <span className={cn("inline-flex rounded-md px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider", channelColor[c.channel] || "bg-secondary")}>
                  {c.channel}
                </span>
                <h3 className="mt-2 truncate text-base font-bold">{c.name}</h3>
              </div>
              <StatusBadge status={c.status} />
            </div>

            <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
              <div className="rounded-lg border border-border p-2.5">
                <div className="flex items-center gap-1 text-[10px] uppercase tracking-wider text-muted-foreground">
                  <Users className="h-3 w-3" /> Audience
                </div>
                <div className="mt-0.5 font-mono text-sm font-semibold">{(c.audience || 0).toLocaleString()}</div>
              </div>
              <div className="rounded-lg border border-border p-2.5">
                <div className="flex items-center gap-1 text-[10px] uppercase tracking-wider text-muted-foreground">
                  <Calendar className="h-3 w-3" /> Schedule
                </div>
                <div className="mt-0.5 truncate text-xs font-medium">{c.schedule || "—"}</div>
              </div>
            </div>

            <div className="mt-4 grid grid-cols-4 gap-2 border-t border-border pt-4">
              <Metric icon={Send} label="Sent" value={(c.sent || 0).toLocaleString()} />
              <Metric icon={CheckCircle2} label="Del." value={(c.delivered || 0).toLocaleString()} />
              <Metric icon={Eye} label="Read" value={(c.opens || 0).toLocaleString()} />
              <Metric icon={Reply} label="Replies" value={(c.replies || 0).toLocaleString()} />
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

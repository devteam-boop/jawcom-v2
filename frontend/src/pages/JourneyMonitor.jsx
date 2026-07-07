import { useMemo, useState, useEffect, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import PageHeader from "@/components/PageHeader";
import SearchBar from "@/components/SearchBar";
import FilterBar from "@/components/FilterBar";
import DataTable from "@/components/DataTable";
import StatusBadge from "@/components/StatusBadge";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
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
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { JourneyList, useJourneys, ExecutionDrawer, INSTANCE_STATUS_TONE } from "@/modules/journeys";
import { runningInstanceService } from "@/services/runningInstances";
import { journeyService } from "@/services/journeys";
import { stageMappingService } from "@/services/stageMappings";
import { toast } from "sonner";
import {
  Workflow,
  Settings,
  Clock,
  RefreshCw,
} from "lucide-react";

const PRIORITIES = ["High", "Medium", "Low"];

function toRow(instance, journeyMap) {
  const leadId = instance.lead_id || "";
  const j = journeyMap[instance.journey_id];
  const data = instance.data || {};
  return {
    id: instance.id,
    journey_id: instance.journey_id,
    lead_id: instance.lead_id,
    name: `Lead #${leadId}`,
    initials: String(leadId).slice(0, 2).toUpperCase() || "??",
    email: "",
    phone: "",
    company: "",
    stage: j?.status || "—",
    journey: j?.name || "Unknown",
    autoStatus: instance.status || "unknown",
    comms: instance.status === "running" ? "Open" : "Closed",
    health: instance.status === "completed" ? "Healthy" : instance.status === "failed" ? "Stalled" : "At Risk",
    messagesSent: 0,
    replies: 0,
    pendingActions: 0,
    owner: "—",
    priority: PRIORITIES[Math.floor(Math.random() * PRIORITIES.length)],
    current_node_id: data.current_node_id || null,
    last_executed_at: data.last_executed_at || null,
    resume_at: data.resume_at || null,
    retry_count: data.retry_count || 0,
    started_at: instance.started_at || null,
    completed_at: instance.completed_at || null,
    lastActivity: instance.updated_at || instance.created_at || "—",
    aiSummary: "",
    healthTone: instance.status === "completed" ? "success" : instance.status === "failed" ? "danger" : "warning",
    data: data,
    timeline: [],
  };
}

const FILTER_TABS = [
  { label: "All", value: "all" },
  { label: "Running", value: "running" },
  { label: "Paused", value: "paused" },
  { label: "Waiting Approval", value: "waiting_approval" },
  { label: "Waiting Task", value: "waiting_task" },
  { label: "Failed", value: "failed" },
];

export default function JourneyMonitor() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [viewMode, setViewMode] = useState("monitor");
  const [search, setSearch] = useState("");
  const [tab, setTab] = useState("all");
  const [journeyFilter, setJourneyFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [instances, setInstances] = useState([]);
  const [journeyMap, setJourneyMap] = useState({});
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState(null);

  const { journeys, loading: journeysLoading, refetch: refetchJourneys } = useJourneys();
  const [mappings, setMappings] = useState([]);
  const [instanceCounts, setInstanceCounts] = useState({});
  const [manageSearch, setManageSearch] = useState("");
  const [manageFilter, setManageFilter] = useState("all");
  const [createOpen, setCreateOpen] = useState(false);
  const [createName, setCreateName] = useState("");
  const [createDesc, setCreateDesc] = useState("");

  const fetchData = useCallback(async () => {
    try {
      const [instancesData, journeysData] = await Promise.all([
        runningInstanceService.list(),
        journeyService.list(),
      ]);
      setInstances(instancesData);
      const map = {};
      journeysData.forEach((j) => { map[j.id] = j; });
      setJourneyMap(map);
    } catch {
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  useEffect(() => {
    const interval = setInterval(() => {
      runningInstanceService.list().then(setInstances).catch(() => {});
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = useCallback(async () => {
    await fetchData();
  }, [fetchData]);

  useEffect(() => {
    if (viewMode !== "manage") return;
    stageMappingService.list().then(setMappings).catch(() => {});
  }, [viewMode]);

  useEffect(() => {
    if (viewMode !== "manage" || !journeys.length) return;
    Promise.all(
      journeys.map(async (j) => {
        try {
          const result = await runningInstanceService.list({ journeyId: j.id });
          return { id: j.id, count: result.length };
        } catch {
          return { id: j.id, count: 0 };
        }
      })
    ).then((results) => {
      const map = {};
      results.forEach((r) => { map[r.id] = r.count; });
      setInstanceCounts(map);
    });
  }, [viewMode, journeys]);

  const enriched = useMemo(() => instances.map((i) => toRow(i, journeyMap)), [instances, journeyMap]);

  const rows = useMemo(() => {
    return enriched.filter((r) => {
      if (tab === "all") {}
      else if (tab === "running" && r.autoStatus !== "running") return false;
      else if (tab === "paused" && r.autoStatus !== "paused" && r.autoStatus !== "waiting") return false;
      else if (tab === "waiting_approval" && r.autoStatus !== "waiting_approval") return false;
      else if (tab === "waiting_task" && r.autoStatus !== "waiting_task") return false;
      else if (tab === "failed" && r.autoStatus !== "failed") return false;
      if (journeyFilter !== "all" && r.journey !== journeyFilter) return false;
      if (statusFilter !== "all" && r.autoStatus !== statusFilter) return false;
      if (search) {
        const q = search.toLowerCase();
        const hay = `${r.name} ${r.journey} ${r.autoStatus} ${String(r.lead_id)} ${r.current_node_id || ""}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }, [enriched, tab, search, journeyFilter, statusFilter]);

  const filterOptions = FILTER_TABS.map((f) => ({
    ...f,
    count: f.value === "all" ? enriched.length : enriched.filter((r) => r.autoStatus === f.value).length,
  }));

  const enrichedJourneys = useMemo(() => {
    if (!journeys.length) return [];
    return journeys.map((j) => ({
      ...j,
      stageMappings: mappings.filter((sm) => sm.journey_id === j.id),
      runningCount: instanceCounts[j.id] || 0,
      health: null,
    }));
  }, [journeys, mappings, instanceCounts]);

  // Deep-link support: /journeys?instance=<id> (used by the Journey
  // Dashboard's Quick Actions / Running tab) auto-opens that instance's
  // detail drawer, then clears the param.
  useEffect(() => {
    const instanceId = searchParams.get("instance");
    if (!instanceId) return;
    setSelectedId(instanceId);
    setSearchParams({}, { replace: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  const handleCreate = async () => {
    if (!createName.trim()) return;
    try {
      await journeyService.create({
        name: createName.trim(),
        description: createDesc.trim() || null,
        trigger_type: "lead_stage_changed",
      });
      setCreateOpen(false);
      setCreateName("");
      setCreateDesc("");
      refetchJourneys();
      toast.success("Journey created");
    } catch (err) {
      toast.error(err.message || "Failed to create journey");
    }
  };

  const columns = [
    {
      key: "name",
      label: "Lead",
      render: (r) => (
        <div className="flex items-center gap-2.5">
          <Avatar className="h-7 w-7">
            <AvatarFallback className="bg-primary/10 text-[10px] font-semibold text-primary">{r.initials}</AvatarFallback>
          </Avatar>
          <div className="min-w-0">
            <div className="truncate text-sm font-semibold">{r.name}</div>
          </div>
        </div>
      ),
    },
    {
      key: "journey",
      label: "Journey",
      render: (r) => (
        <div className="flex items-center gap-1.5 whitespace-nowrap text-xs">
          <Workflow className="h-3 w-3 text-primary" /> {r.journey}
        </div>
      ),
    },
    { key: "autoStatus", label: "Status", render: (r) => <StatusBadge status={r.autoStatus} tone={INSTANCE_STATUS_TONE[r.autoStatus]} /> },
    {
      key: "health",
      label: "Health",
      render: (r) => <StatusBadge status={r.health === "Healthy" ? "Active" : r.health === "At Risk" ? "Open" : "Lost"} tone={r.healthTone} />,
    },
    {
      key: "current_node_id",
      label: "Current Node",
      render: (r) => (
        <span className="flex items-center gap-1 whitespace-nowrap text-xs">
          <Clock className="h-3 w-3 text-muted-foreground" />
          {r.current_node_id || (r.autoStatus === "completed" ? "Completed" : r.autoStatus === "failed" ? "Failed" : "—")}
        </span>
      ),
    },
    { key: "lastActivity", label: "Last Activity", render: (r) => <span className="whitespace-nowrap text-xs text-muted-foreground">{r.lastActivity}</span> },
  ];

  if (loading) {
    return (
      <div data-testid="page-journeys">
        <PageHeader title="Journeys" description="Monitor running instances and manage journey definitions." />
        <div className="flex items-center justify-center p-12 text-sm text-muted-foreground">Loading…</div>
      </div>
    );
  }

  return (
    <div data-testid="page-journeys">
      <PageHeader
        title={viewMode === "monitor" ? "Journey Monitor" : "Manage Journeys"}
        description={
          viewMode === "monitor"
            ? "Every contact, in real time, across every automated journey."
            : "Create, edit, and manage your journey definitions."
        }
        actions={
          viewMode === "monitor" ? (
            <div className="flex items-center gap-2">
              <Button size="sm" variant="outline" onClick={handleRefresh}>
                <RefreshCw className="mr-2 h-3.5 w-3.5" /> Refresh
              </Button>
              <Button size="sm" variant="outline" onClick={() => setViewMode("manage")}>
                <Settings className="mr-2 h-3.5 w-3.5" /> Manage Journeys
              </Button>
            </div>
          ) : (
            <Button size="sm" variant="outline" onClick={() => setViewMode("monitor")}>
              <Workflow className="mr-2 h-3.5 w-3.5" /> Running Monitor
            </Button>
          )
        }
      />

      {viewMode === "monitor" ? (
        <>
          <div className="space-y-4 px-4 py-6 md:px-8">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <SearchBar
                value={search}
                onChange={setSearch}
                placeholder="Search lead, journey, status…"
                className="w-full sm:max-w-sm"
                testId="journey-monitor-search"
              />
              <FilterBar options={filterOptions} value={tab} onChange={setTab} testId="journey-monitor-tabs" />
            </div>

            <div className="flex flex-wrap items-center gap-2 rounded-xl border border-border bg-card p-3">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Filters</span>
              <FilterSelect label="Journey" value={journeyFilter} onChange={setJourneyFilter} options={["all", ...Array.from(new Set(enriched.map((r) => r.journey)))]} />
              <FilterSelect label="Status" value={statusFilter} onChange={setStatusFilter} options={["all", "running", "paused", "completed", "failed", "waiting"]} />
            </div>

            <DataTable columns={columns} rows={rows} onRowClick={(row) => setSelectedId(row.id)} testId="journey-monitor-table" />
          </div>

          <ExecutionDrawer
            instanceId={selectedId}
            onClose={() => setSelectedId(null)}
            onActionComplete={fetchData}
          />
        </>
      ) : (
        <div className="space-y-4 px-4 py-6 md:px-8">
          {journeysLoading ? (
            <div className="flex items-center justify-center p-12 text-sm text-muted-foreground">Loading journeys…</div>
          ) : (
            <JourneyList
              journeys={enrichedJourneys}
              search={manageSearch}
              onSearchChange={setManageSearch}
              filter={manageFilter}
              onFilterChange={setManageFilter}
              onCreate={() => setCreateOpen(true)}
            />
          )}
        </div>
      )}

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Journey</DialogTitle>
            <DialogDescription>Define a new automated journey for your leads.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-1.5">
              <Label htmlFor="name">Name</Label>
              <Input id="name" value={createName} onChange={(e) => setCreateName(e.target.value)} placeholder="e.g. Lead Qualification" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="desc">Description</Label>
              <Input id="desc" value={createDesc} onChange={(e) => setCreateDesc(e.target.value)} placeholder="Optional description" />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>Cancel</Button>
            <Button onClick={handleCreate}>Create</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function FilterSelect({ label, value, onChange, options }) {
  return (
    <div className="flex items-center gap-1.5">
      <span className="text-[11px] text-muted-foreground">{label}</span>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger className="h-7 min-w-[110px] text-xs">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {options.map((o) => (
            <SelectItem key={o} value={o} className="text-xs">{o === "all" ? "All" : o}</SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}

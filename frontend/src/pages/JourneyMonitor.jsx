<<<<<<< HEAD
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

export default function JourneyMonitor() {
  const navigate = useNavigate();
  useEffect(() => { navigate("/journeys", { replace: true }); }, [navigate]);
  return null;
=======
import { useMemo, useState } from "react";
import PageHeader from "@/components/PageHeader";
import SearchBar from "@/components/SearchBar";
import FilterBar from "@/components/FilterBar";
import DataTable from "@/components/DataTable";
import StatusBadge from "@/components/StatusBadge";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import {
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { CUSTOMERS, TIMELINE } from "@/dummy-data";
import { COMPANIES } from "@/dummy-data/companies";
import {
  Sparkles,
  Zap,
  Workflow,
  Phone,
  Mail,
  MessageCircle,
  Clock,
  Pause,
  Play,
} from "lucide-react";

const JOURNEYS_LIST = ["Welcome Series", "Lead Qualification", "Visit Reminder", "Proposal Follow-up", "Renewal", "Onboarding"];
const AUTOS = ["Running", "Paused", "Draft", "Completed"];
const COMMS = ["Unread", "Open", "Closed", "Assigned"];
const PRIORITIES = ["High", "Medium", "Low"];
const OWNERS = ["Maya Iyer", "Rohan Mehta", "Ana Souza", "Kenji Watanabe"];
const HEALTH_TONE = { Healthy: "success", "At Risk": "warning", Stalled: "danger" };
const HEALTHS = ["Healthy", "Healthy", "At Risk", "Healthy", "Stalled"];
const NEXT_STEPS = ["Send WhatsApp template", "AI Decision", "Assign AE", "Wait 2 days", "Send pricing email"];

const priorityTone = { High: "danger", Medium: "info", Low: "neutral" };

function toRow(c, i) {
  const co = COMPANIES.find((x) => x.name === c.company);
  const journey = JOURNEYS_LIST[i % JOURNEYS_LIST.length];
  return {
    ...c,
    companyRef: co,
    journey,
    autoStatus: AUTOS[i % AUTOS.length],
    comms: COMMS[i % COMMS.length],
    health: HEALTHS[i % HEALTHS.length],
    messagesSent: 8 + ((i * 3) % 22),
    replies: 1 + ((i * 2) % 9),
    pendingActions: (i % 3) + 1,
    priority: PRIORITIES[i % PRIORITIES.length],
    nextAutomation: NEXT_STEPS[i % NEXT_STEPS.length],
    lastActivity: c.lastContact,
    phone: `+91 98${String(10000 + i * 137).slice(0, 6)}`,
  };
}

const FILTER_TABS = [
  { label: "All", value: "all" },
  { label: "Running", value: "Running" },
  { label: "Paused", value: "Paused" },
  { label: "At Risk", value: "AtRisk" },
];

export default function JourneyMonitor() {
  const [search, setSearch] = useState("");
  const [tab, setTab] = useState("all");
  const [leadStage, setLeadStage] = useState("all");
  const [journey, setJourney] = useState("all");
  const [owner, setOwner] = useState("all");
  const [priority, setPriority] = useState("all");
  const [company, setCompany] = useState("all");
  const [selected, setSelected] = useState(null);

  const enriched = useMemo(() => CUSTOMERS.map(toRow), []);

  const rows = useMemo(() => {
    return enriched.filter((r) => {
      if (tab === "Running" && r.autoStatus !== "Running") return false;
      if (tab === "Paused" && r.autoStatus !== "Paused") return false;
      if (tab === "AtRisk" && r.health !== "At Risk") return false;
      if (leadStage !== "all" && r.stage !== leadStage) return false;
      if (journey !== "all" && r.journey !== journey) return false;
      if (owner !== "all" && r.owner !== owner) return false;
      if (priority !== "all" && r.priority !== priority) return false;
      if (company !== "all" && r.company !== company) return false;
      if (search) {
        const q = search.toLowerCase();
        const hay = `${r.name} ${r.company} ${r.email} ${r.phone}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }, [enriched, tab, leadStage, journey, owner, priority, company, search]);

  const filterOptions = FILTER_TABS.map((f) => ({
    ...f,
    count:
      f.value === "all"
        ? enriched.length
        : f.value === "AtRisk"
        ? enriched.filter((r) => r.health === "At Risk").length
        : enriched.filter((r) => r.autoStatus === f.value).length,
  }));

  const stageOptions = ["all", ...Array.from(new Set(enriched.map((r) => r.stage)))];
  const journeyOptions = ["all", ...JOURNEYS_LIST];
  const ownerOptions = ["all", ...OWNERS];
  const priorityOptions = ["all", ...PRIORITIES];
  const companyOptions = ["all", ...Array.from(new Set(enriched.map((r) => r.company)))];

  const columns = [
    {
      key: "name",
      label: "Customer",
      render: (r) => (
        <div className="flex items-center gap-2.5">
          <Avatar className="h-7 w-7">
            <AvatarFallback className="bg-primary/10 text-[10px] font-semibold text-primary">{r.initials}</AvatarFallback>
          </Avatar>
          <div className="min-w-0">
            <div className="truncate text-sm font-semibold">{r.name}</div>
            <div className="truncate text-[10px] text-muted-foreground">{r.email}</div>
          </div>
        </div>
      ),
    },
    { key: "company", label: "Company", render: (r) => <span className="whitespace-nowrap text-sm">{r.company}</span> },
    { key: "stage", label: "Lead Stage", render: (r) => <StatusBadge status={r.stage} /> },
    {
      key: "journey",
      label: "Current Journey",
      render: (r) => (
        <div className="flex items-center gap-1.5 whitespace-nowrap text-xs">
          <Zap className="h-3 w-3 text-primary" /> {r.journey}
        </div>
      ),
    },
    { key: "autoStatus", label: "Automation", render: (r) => <StatusBadge status={r.autoStatus === "Running" ? "Active" : r.autoStatus} /> },
    { key: "comms", label: "Conversation", render: (r) => <StatusBadge status={r.comms} /> },
    {
      key: "health",
      label: "Health",
      render: (r) => <StatusBadge status={r.health === "Healthy" ? "Active" : r.health === "At Risk" ? "Open" : "Lost"} tone={HEALTH_TONE[r.health]} />,
    },
    { key: "messagesSent", label: "Sent", render: (r) => <span className="font-mono text-xs font-semibold">{r.messagesSent}</span> },
    { key: "replies", label: "Replies", render: (r) => <span className="font-mono text-xs font-semibold">{r.replies}</span> },
    {
      key: "pendingActions",
      label: "Pending",
      render: (r) => (
        <span className="inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-primary/10 px-1.5 font-mono text-[10px] font-semibold text-primary">
          {r.pendingActions}
        </span>
      ),
    },
    { key: "owner", label: "Owner", render: (r) => <span className="whitespace-nowrap text-xs">{r.owner}</span> },
    {
      key: "aiSummary",
      label: "AI Summary",
      render: (r) => (
        <span className="line-clamp-1 max-w-[220px] text-xs text-muted-foreground">
          {r.health === "Healthy" ? "On track — high intent" : r.health === "At Risk" ? "Stalled — needs nudge" : "No reply in 14 days"}
        </span>
      ),
    },
    {
      key: "nextAutomation",
      label: "Next Automation",
      render: (r) => (
        <span className="flex items-center gap-1 whitespace-nowrap text-xs">
          <Clock className="h-3 w-3 text-muted-foreground" />
          {r.nextAutomation}
        </span>
      ),
    },
    { key: "lastActivity", label: "Last Activity", render: (r) => <span className="whitespace-nowrap text-xs text-muted-foreground">{r.lastActivity}</span> },
    {
      key: "timeline",
      label: "Timeline",
      render: (r) => (
        <div className="flex items-center gap-0.5">
          {[0, 1, 2, 3, 4].map((i) => (
            <span
              key={i}
              className={`h-3 w-1.5 rounded-sm ${
                i < Math.min(4, Math.floor(r.messagesSent / 6))
                  ? "bg-primary"
                  : "bg-secondary"
              }`}
            />
          ))}
        </div>
      ),
    },
  ];

  return (
    <div data-testid="page-journey-monitor">
      <PageHeader
        title="Journey Monitor"
        description="Every contact, in real time, across every automated journey."
      />

      <div className="space-y-4 px-4 py-6 md:px-8">
        {/* Search + tabs */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <SearchBar
            value={search}
            onChange={setSearch}
            placeholder="Search customer, company, phone, email…"
            className="w-full sm:max-w-sm"
            testId="journey-monitor-search"
          />
          <FilterBar options={filterOptions} value={tab} onChange={setTab} testId="journey-monitor-tabs" />
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-2 rounded-xl border border-border bg-card p-3">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Filters</span>
          <FilterSelect label="Lead Stage" value={leadStage} onChange={setLeadStage} options={stageOptions} />
          <FilterSelect label="Journey" value={journey} onChange={setJourney} options={journeyOptions} />
          <FilterSelect label="Owner" value={owner} onChange={setOwner} options={ownerOptions} />
          <FilterSelect label="Automation" value={tab} onChange={setTab} options={["all", "Running", "Paused", "Draft", "Completed"]} />
          <FilterSelect label="Priority" value={priority} onChange={setPriority} options={priorityOptions} />
          <FilterSelect label="Company" value={company} onChange={setCompany} options={companyOptions} />
        </div>

        <DataTable columns={columns} rows={rows} onRowClick={setSelected} testId="journey-monitor-table" />
      </div>

      <Sheet open={!!selected} onOpenChange={(open) => !open && setSelected(null)}>
        <SheetContent side="right" className="w-full overflow-y-auto p-0 sm:max-w-md">
          {selected && (
            <>
              <SheetHeader className="border-b border-border p-6">
                <div className="flex items-start gap-4">
                  <Avatar className="h-14 w-14">
                    <AvatarFallback className="bg-primary/10 text-base font-semibold text-primary">{selected.initials}</AvatarFallback>
                  </Avatar>
                  <div className="min-w-0 flex-1 text-left">
                    <SheetTitle className="truncate text-lg">{selected.name}</SheetTitle>
                    <p className="truncate text-sm text-muted-foreground">{selected.company}</p>
                    <p className="truncate text-xs text-muted-foreground">{selected.phone} · {selected.email}</p>
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      <StatusBadge status={selected.autoStatus === "Running" ? "Active" : selected.autoStatus} />
                      <StatusBadge status={selected.health === "Healthy" ? "Active" : selected.health === "At Risk" ? "Open" : "Lost"} tone={HEALTH_TONE[selected.health]} />
                      <StatusBadge status={selected.priority === "High" ? "Overdue" : selected.priority === "Medium" ? "Open" : "Completed"} tone={priorityTone[selected.priority]} />
                    </div>
                  </div>
                </div>
                <div className="mt-4 flex gap-2">
                  <Button size="sm" className="flex-1">
                    <MessageCircle className="mr-2 h-3.5 w-3.5" /> WhatsApp
                  </Button>
                  <Button size="sm" variant="outline" className="flex-1">
                    <Phone className="mr-2 h-3.5 w-3.5" /> Call
                  </Button>
                </div>
              </SheetHeader>

              <Tabs defaultValue="journey" className="p-6">
                <TabsList className="grid w-full grid-cols-4">
                  <TabsTrigger value="journey" className="text-xs">Journey</TabsTrigger>
                  <TabsTrigger value="steps" className="text-xs">Steps</TabsTrigger>
                  <TabsTrigger value="timeline" className="text-xs">Timeline</TabsTrigger>
                  <TabsTrigger value="ai" className="text-xs">AI</TabsTrigger>
                </TabsList>

                <TabsContent value="journey" className="mt-5 space-y-3 text-sm">
                  <div className="rounded-lg border border-border bg-card p-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Workflow className="h-3.5 w-3.5 text-primary" />
                        <span className="text-sm font-semibold">{selected.journey}</span>
                      </div>
                      <StatusBadge status={selected.autoStatus === "Running" ? "Active" : selected.autoStatus} />
                    </div>
                    <div className="mt-2 flex items-center gap-3 text-[11px] text-muted-foreground">
                      <span><span className="font-mono font-semibold text-foreground">{selected.messagesSent}</span> sent</span>
                      <span>·</span>
                      <span><span className="font-mono font-semibold text-foreground">{selected.replies}</span> replies</span>
                      <span>·</span>
                      <span><span className="font-mono font-semibold text-foreground">{selected.pendingActions}</span> pending</span>
                    </div>
                  </div>
                  <MetaRow label="Lead stage" value={selected.stage} />
                  <MetaRow label="Owner" value={selected.owner} />
                  <MetaRow label="Priority" value={selected.priority} />
                  <MetaRow label="Health" value={selected.health} />
                  <MetaRow label="Next automation" value={selected.nextAutomation} />
                  <Separator />
                  <div className="flex flex-col gap-1.5">
                    <Button variant="outline" size="sm" className="h-8 justify-start text-xs">
                      <Pause className="mr-2 h-3 w-3" /> Pause journey
                    </Button>
                    <Button variant="outline" size="sm" className="h-8 justify-start text-xs">
                      <Play className="mr-2 h-3 w-3" /> Move to different journey
                    </Button>
                  </div>
                </TabsContent>

                <TabsContent value="steps" className="mt-5 space-y-2">
                  {[
                    { name: "Trigger · New conversation", state: "done" },
                    { name: "AI Decision · Intent classifier", state: "done" },
                    { name: "Send WhatsApp template", state: "done" },
                    { name: "Wait 2 days", state: "current" },
                    { name: "Send pricing email", state: "upcoming" },
                    { name: "Assign AE", state: "upcoming" },
                  ].map((s, i) => (
                    <div key={i} className="flex items-center gap-3 rounded-lg border border-border p-2.5">
                      <span
                        className={`inline-block h-2.5 w-2.5 rounded-full ${
                          s.state === "done"
                            ? "bg-emerald-500"
                            : s.state === "current"
                            ? "bg-primary"
                            : "bg-secondary"
                        }`}
                      />
                      <span className={`text-sm ${s.state === "upcoming" ? "text-muted-foreground" : "font-medium"}`}>{s.name}</span>
                    </div>
                  ))}
                </TabsContent>

                <TabsContent value="timeline" className="mt-5">
                  <ol className="relative space-y-4 border-l border-border pl-5">
                    {TIMELINE.map((t) => (
                      <li key={t.id} className="relative">
                        <span className="absolute -left-[26px] top-1 flex h-3 w-3 items-center justify-center rounded-full border-2 border-background bg-primary" />
                        <div className="text-xs text-muted-foreground">{t.time}</div>
                        <p className="text-sm">{t.text}</p>
                      </li>
                    ))}
                  </ol>
                </TabsContent>

                <TabsContent value="ai" className="mt-5">
                  <div className="rounded-lg border border-primary/30 bg-primary/5 p-4">
                    <div className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-primary">
                      <Sparkles className="h-3.5 w-3.5" /> AI Summary
                    </div>
                    <p className="text-sm leading-relaxed">
                      {selected.name} is currently on the {selected.journey.toLowerCase()} track. Health is {selected.health.toLowerCase()}. The next scheduled step is “{selected.nextAutomation}”. Reply rate is {Math.round((selected.replies / Math.max(1, selected.messagesSent)) * 100)}%.
                    </p>
                  </div>
                </TabsContent>
              </Tabs>
            </>
          )}
        </SheetContent>
      </Sheet>
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

function MetaRow({ label, value }) {
  return (
    <div className="flex items-center justify-between border-b border-border/60 pb-2 text-sm">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
>>>>>>> 321075ad65aa3df54916ae638505753705e9661b
}

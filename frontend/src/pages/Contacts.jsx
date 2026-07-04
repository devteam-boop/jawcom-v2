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
import { CUSTOMERS, TIMELINE } from "@/dummy-data";
import { COMPANIES, COMPANY_JOURNEY } from "@/dummy-data/companies";
import {
  Download,
  Plus,
  Mail,
  Phone,
  Sparkles,
  StickyNote,
  Workflow,
  Calendar,
  Globe,
  MessageCircle,
  Zap,
  Building2,
} from "lucide-react";

const FILTERS = [
  { label: "All", value: "all" },
  { label: "Active", value: "Active" },
  { label: "Lead", value: "Lead" },
  { label: "Inactive", value: "Inactive" },
];

const COMMS = ["Unread", "Open", "Closed", "Assigned"];
const AUTOS = ["Running", "Paused", "Draft", "Completed"];
const JOURNEYS_NAMES = ["Welcome Series", "Lead Qualification", "Visit Reminder", "Proposal Follow-up", "Renewal", "Onboarding"];
const LAST_MSGS = [
  "Yes, the proposal looks great — can we hop on a quick call?",
  "Thanks Maya. I'll loop in our procurement team this week.",
  "Could you share the integration docs again? 🙏",
  "Our team just finished onboarding — first impressions are great.",
  "Pricing is a bit higher than expected — any flexibility?",
];
const PRIORITIES = ["High", "Medium", "Low"];

const priorityTone = { High: "danger", Medium: "info", Low: "neutral" };

function enrich(c, i) {
  const company = COMPANIES.find((co) => co.name === c.company);
  return {
    ...c,
    companyRef: company,
    comms: COMMS[i % COMMS.length],
    autoStatus: AUTOS[i % AUTOS.length],
    currentJourney: JOURNEYS_NAMES[i % JOURNEYS_NAMES.length],
    lastMessage: LAST_MSGS[i % LAST_MSGS.length],
    aiScore: 55 + ((i * 7) % 42),
    priority: PRIORITIES[i % PRIORITIES.length],
  };
}

export default function Contacts() {
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");
  const [selected, setSelected] = useState(null);

  const enriched = useMemo(() => CUSTOMERS.map(enrich), []);

  const rows = useMemo(() => {
    return enriched.filter((c) => {
      if (filter !== "all" && c.status !== filter) return false;
      if (search && !`${c.name} ${c.company} ${c.email}`.toLowerCase().includes(search.toLowerCase())) return false;
      return true;
    });
  }, [enriched, search, filter]);

  const columns = [
    {
      key: "name",
      label: "Customer",
      render: (r) => (
        <div className="flex items-center gap-3">
          <Avatar className="h-8 w-8">
            <AvatarFallback className="bg-primary/10 text-[11px] font-semibold text-primary">
              {r.initials}
            </AvatarFallback>
          </Avatar>
          <div className="min-w-0">
            <div className="truncate text-sm font-semibold">{r.name}</div>
            <div className="truncate text-xs text-muted-foreground">{r.email}</div>
          </div>
        </div>
      ),
    },
    { key: "company", label: "Company", render: (r) => <span className="whitespace-nowrap text-sm">{r.company}</span> },
    { key: "stage", label: "Lead Stage", render: (r) => <StatusBadge status={r.stage} /> },
    { key: "owner", label: "Owner", render: (r) => <span className="whitespace-nowrap text-sm">{r.owner}</span> },
    { key: "comms", label: "Comm. Status", render: (r) => <StatusBadge status={r.comms} /> },
    { key: "autoStatus", label: "Automation", render: (r) => <StatusBadge status={r.autoStatus === "Running" ? "Active" : r.autoStatus} /> },
    {
      key: "currentJourney",
      label: "Current Journey",
      render: (r) => (
        <div className="flex items-center gap-1.5 whitespace-nowrap text-xs">
          <Zap className="h-3 w-3 text-primary" /> {r.currentJourney}
        </div>
      ),
    },
    {
      key: "lastMessage",
      label: "Last Message",
      render: (r) => (
        <span className="line-clamp-1 max-w-[240px] text-xs text-muted-foreground">{r.lastMessage}</span>
      ),
    },
    {
      key: "aiScore",
      label: "AI Score",
      render: (r) => (
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs font-semibold">{r.aiScore}</span>
          <div className="h-1.5 w-14 overflow-hidden rounded-full bg-secondary">
            <div className="h-full rounded-full bg-primary" style={{ width: `${r.aiScore}%` }} />
          </div>
        </div>
      ),
    },
    { key: "lastContact", label: "Last Activity", render: (r) => <span className="whitespace-nowrap text-xs text-muted-foreground">{r.lastContact} · {r.channel}</span> },
    { key: "priority", label: "Priority", render: (r) => <StatusBadge status={r.priority === "High" ? "Overdue" : r.priority === "Medium" ? "Open" : "Completed"} tone={priorityTone[r.priority]} /> },
  ];

  const filterOptions = FILTERS.map((f) => ({
    ...f,
    count: f.value === "all" ? CUSTOMERS.length : CUSTOMERS.filter((c) => c.status === f.value).length,
  }));

  return (
    <div data-testid="page-contacts">
      <PageHeader
        title="Contacts"
        description={`${CUSTOMERS.length} people across ${COMPANIES.length} companies`}
        actions={
          <>
            <Button variant="outline" size="sm" data-testid="contacts-export">
              <Download className="mr-2 h-3.5 w-3.5" /> Export
            </Button>
            <Button size="sm" data-testid="contacts-add">
              <Plus className="mr-2 h-3.5 w-3.5" /> Add contact
            </Button>
          </>
        }
      />

      <div className="space-y-4 px-4 py-6 md:px-8">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <SearchBar
            value={search}
            onChange={setSearch}
            placeholder="Search by name, company, email…"
            className="w-full sm:max-w-sm"
            testId="contacts-search"
          />
          <FilterBar options={filterOptions} value={filter} onChange={setFilter} testId="contacts-filter" />
        </div>

        <DataTable columns={columns} rows={rows} onRowClick={setSelected} testId="contacts-table" />
      </div>

      <Sheet open={!!selected} onOpenChange={(open) => !open && setSelected(null)}>
        <SheetContent side="right" className="w-full overflow-y-auto p-0 sm:max-w-md">
          {selected && (
            <>
              <SheetHeader className="border-b border-border p-6">
                <div className="flex items-start gap-4">
                  <Avatar className="h-14 w-14">
                    <AvatarFallback className="bg-primary/10 text-base font-semibold text-primary">
                      {selected.initials}
                    </AvatarFallback>
                  </Avatar>
                  <div className="min-w-0 flex-1 text-left">
                    <SheetTitle className="truncate text-lg">{selected.name}</SheetTitle>
                    <p className="truncate text-sm text-muted-foreground">{selected.company}</p>
                    <p className="truncate text-xs text-muted-foreground">{selected.email}</p>
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      <StatusBadge status={selected.status} />
                      <StatusBadge status={selected.stage} />
                      <StatusBadge status={selected.priority === "High" ? "Overdue" : selected.priority === "Medium" ? "Open" : "Completed"} tone={priorityTone[selected.priority]} />
                    </div>
                  </div>
                </div>
                <div className="mt-4 flex gap-2">
                  <Button size="sm" className="flex-1">
                    <Mail className="mr-2 h-3.5 w-3.5" /> Email
                  </Button>
                  <Button size="sm" variant="outline" className="flex-1">
                    <Phone className="mr-2 h-3.5 w-3.5" /> Call
                  </Button>
                </div>
              </SheetHeader>

              <Tabs defaultValue="overview" className="p-6">
                <TabsList className="grid w-full grid-cols-7">
                  <TabsTrigger value="overview" className="text-xs">Over.</TabsTrigger>
                  <TabsTrigger value="conversation" className="text-xs">Conv.</TabsTrigger>
                  <TabsTrigger value="automation" className="text-xs">Auto.</TabsTrigger>
                  <TabsTrigger value="timeline" className="text-xs">Time.</TabsTrigger>
                  <TabsTrigger value="notes" className="text-xs">Notes</TabsTrigger>
                  <TabsTrigger value="ai" className="text-xs">AI</TabsTrigger>
                  <TabsTrigger value="company" className="text-xs">Comp.</TabsTrigger>
                </TabsList>

                <TabsContent value="overview" className="mt-5 space-y-3 text-sm">
                  <Detail label="Owner" value={selected.owner} />
                  <Detail label="Lead stage" value={selected.stage} />
                  <Detail label="Primary channel" value={selected.channel} />
                  <Detail label="Last contact" value={selected.lastContact} />
                  <Detail label="AI score" value={`${selected.aiScore}`} />
                  <Detail label="Priority" value={selected.priority} />
                  <Separator />
                  <div>
                    <div className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                      Tags
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {selected.tags.map((t) => (
                        <span key={t} className="rounded-md bg-secondary px-2 py-0.5 text-xs font-medium">
                          #{t}
                        </span>
                      ))}
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="conversation" className="mt-5 space-y-2">
                  {[
                    { id: "tc1", channel: "WhatsApp", preview: selected.lastMessage, time: "Today · 10:42 AM", status: selected.comms },
                    { id: "tc2", channel: "Email", preview: "Thanks for the deck — sharing internally now.", time: "Feb 8", status: "Open" },
                    { id: "tc3", channel: "WhatsApp", preview: "Following up on the demo recap.", time: "Feb 4", status: "Closed" },
                  ].map((t) => (
                    <div key={t.id} className="rounded-lg border border-border p-3">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">{t.channel}</span>
                        <StatusBadge status={t.status} />
                      </div>
                      <p className="mt-1.5 line-clamp-2 text-sm">{t.preview}</p>
                      <p className="mt-1 text-xs text-muted-foreground">{t.time}</p>
                    </div>
                  ))}
                </TabsContent>

                <TabsContent value="automation" className="mt-5 space-y-3 text-sm">
                  <div className="rounded-lg border border-border bg-card p-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Zap className="h-3.5 w-3.5 text-primary" />
                        <span className="text-sm font-semibold">{selected.currentJourney}</span>
                      </div>
                      <StatusBadge status={selected.autoStatus === "Running" ? "Active" : selected.autoStatus} />
                    </div>
                    <div className="mt-2 flex items-center gap-3 text-[11px] text-muted-foreground">
                      <span><span className="font-mono font-semibold text-foreground">3</span> sent</span>
                      <span>·</span>
                      <span><span className="font-mono font-semibold text-foreground">2</span> replies</span>
                      <span>·</span>
                      <span>Next in <span className="font-mono font-semibold text-foreground">4h</span></span>
                    </div>
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <Button variant="outline" size="sm" className="h-8 justify-start text-xs">Pause automation</Button>
                    <Button variant="outline" size="sm" className="h-8 justify-start text-xs">Move to different journey</Button>
                    <Button variant="outline" size="sm" className="h-8 justify-start text-xs">AI On/Off</Button>
                  </div>
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

                <TabsContent value="notes" className="mt-5 space-y-2">
                  <div className="rounded-lg border border-border bg-card p-3">
                    <div className="flex items-center gap-1.5 text-xs font-semibold">
                      <StickyNote className="h-3 w-3" /> Maya Iyer · Feb 8
                    </div>
                    <p className="mt-1.5 text-sm">Budget confirmed at the upper bracket. Wants Q1 close.</p>
                  </div>
                  <div className="rounded-lg border border-border bg-card p-3">
                    <div className="flex items-center gap-1.5 text-xs font-semibold">
                      <StickyNote className="h-3 w-3" /> Rohan Mehta · Feb 5
                    </div>
                    <p className="mt-1.5 text-sm">Has 2 stakeholders on procurement side.</p>
                  </div>
                </TabsContent>

                <TabsContent value="ai" className="mt-5">
                  <div className="rounded-lg border border-primary/30 bg-primary/5 p-4">
                    <div className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-primary">
                      <Sparkles className="h-3.5 w-3.5" /> AI Summary
                    </div>
                    <p className="text-sm leading-relaxed">
                      {selected.name} has shown consistent engagement across email and chat. Sentiment is highly positive (84%) and reply latency is under 4 minutes. Recommended next action: send the analytics module Loom and schedule a 30-minute call this week.
                    </p>
                  </div>
                  <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                    <Insight label="Sentiment" value="84% positive" />
                    <Insight label="Win likelihood" value={`${selected.aiScore}%`} />
                    <Insight label="Avg. response" value="3m 42s" />
                    <Insight label="Touchpoints" value="14" />
                  </div>
                </TabsContent>

                <TabsContent value="company" className="mt-5">
                  {selected.companyRef ? (
                    <>
                      <div className="flex items-start gap-3 rounded-lg border border-border bg-card p-4">
                        <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-primary/10 text-[11px] font-bold text-primary">
                          {selected.companyRef.logo}
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="text-sm font-bold">{selected.companyRef.name}</div>
                          <div className="text-xs text-muted-foreground">{selected.companyRef.industry} · {selected.companyRef.size}</div>
                          <a href={`https://${selected.companyRef.website}`} className="mt-0.5 inline-flex items-center gap-1 truncate text-xs text-primary hover:underline">
                            <Globe className="h-3 w-3" /> {selected.companyRef.website}
                          </a>
                        </div>
                      </div>
                      <div className="mt-3 grid grid-cols-3 gap-2">
                        <MiniStat label="Contacts" value={selected.companyRef.contacts} />
                        <MiniStat label="ARR" value={selected.companyRef.arr} />
                        <MiniStat label="Open conv." value={selected.companyRef.openConvos} />
                      </div>
                      <Separator className="my-4" />
                      <div className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                        Journey timeline
                      </div>
                      <ol className="relative space-y-3 border-l border-border pl-5">
                        {COMPANY_JOURNEY.map((j) => (
                          <li key={j.id} className="relative">
                            <span
                              className={`absolute -left-[26px] top-1 flex h-3 w-3 items-center justify-center rounded-full border-2 border-background ${
                                j.status === "done"
                                  ? "bg-emerald-500"
                                  : j.status === "current"
                                  ? "bg-primary"
                                  : "bg-secondary"
                              }`}
                            />
                            <div className="flex items-center justify-between">
                              <span className="text-sm font-semibold">{j.stage}</span>
                              <span className="text-xs text-muted-foreground">{j.time}</span>
                            </div>
                            <p className="text-xs text-muted-foreground">{j.note}</p>
                          </li>
                        ))}
                      </ol>
                    </>
                  ) : (
                    <div className="rounded-lg border border-dashed border-border p-6 text-center text-sm text-muted-foreground">
                      <Building2 className="mx-auto mb-2 h-5 w-5" />
                      No company record linked to {selected.name}
                    </div>
                  )}
                </TabsContent>
              </Tabs>
            </>
          )}
        </SheetContent>
      </Sheet>
    </div>
  );
}

function Detail({ label, value }) {
  return (
    <div className="flex items-center justify-between border-b border-border/60 pb-2">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className="text-sm font-medium">{value}</span>
    </div>
  );
}

function Insight({ label, value }) {
  return (
    <div className="rounded-lg border border-border p-3">
      <div className="text-[11px] uppercase tracking-wider text-muted-foreground">{label}</div>
      <div className="mt-1 font-mono text-sm font-semibold">{value}</div>
    </div>
  );
}

function MiniStat({ label, value }) {
  return (
    <div className="rounded-lg border border-border p-2.5">
      <div className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
      <div className="mt-0.5 font-mono text-sm font-semibold">{value}</div>
    </div>
  );
}

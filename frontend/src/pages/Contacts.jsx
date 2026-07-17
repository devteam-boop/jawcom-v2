import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import PageHeader from "@/components/PageHeader";
import SearchBar from "@/components/SearchBar";
import FilterBar from "@/components/FilterBar";
import DataTable from "@/components/DataTable";
import EmptyState from "@/components/EmptyState";
import LoadingSkeleton from "@/components/LoadingSkeleton";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { useConversations, useLeadSummaries, previewFor, ChannelBadge } from "@/modules/inbox";
import { runningInstanceService } from "@/services/runningInstances";
import { journeyService } from "@/services/journeys";
import { formatRelative } from "@/lib/dateFormat";
import { Users } from "lucide-react";

const FILTERS = [
  { label: "All", value: "all" },
  { label: "WhatsApp", value: "whatsapp" },
  { label: "Email", value: "email" },
];

/**
 * "Contacts" is now Communication Contacts: every lead JawCom has any
 * communication_events activity for, derived from the exact same data as
 * the Inbox (useConversations) — not a separate CRM data source, per
 * architecture (JawCom is not a CRM; JAWIS owns leads). Name/phone/email
 * come from the new GET /api/leads/{id}/summary (Phase 2's one new
 * endpoint). Company/tags/assigned user are not shown — JAWIS's lead
 * lookup no longer returns them to anyone (see JawisClient.get_lead
 * docstring), so there is nothing real to display there.
 *
 * Clicking a row opens the Inbox conversation directly (/conversations?lead=id)
 * — there is no separate contact profile screen.
 */
export default function Contacts() {
  const navigate = useNavigate();
  const { conversations, loading } = useConversations();
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");
  const [instancesByLead, setInstancesByLead] = useState({});
  const [journeyMap, setJourneyMap] = useState({});

  const leadIds = useMemo(() => conversations.map((c) => c.leadId), [conversations]);
  const leadSummaries = useLeadSummaries(leadIds);

  useEffect(() => {
    const loadJourneyStatus = () => {
      Promise.all([
        runningInstanceService.list({ limit: 500 }),
        journeyService.list({ limit: 200 }),
      ])
        .then(([instances, journeys]) => {
          const byLead = {};
          instances.forEach((i) => {
            const existing = byLead[i.lead_id];
            if (!existing || new Date(i.started_at) > new Date(existing.started_at)) byLead[i.lead_id] = i;
          });
          setInstancesByLead(byLead);
          setJourneyMap(Object.fromEntries(journeys.map((j) => [j.id, j])));
        })
        .catch(() => {});
    };
    loadJourneyStatus();
    const interval = setInterval(loadJourneyStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  const PAGE_SIZE = 25;
  const [page, setPage] = useState(1);
  useEffect(() => { setPage(1); }, [search, filter]);

  const allRows = useMemo(() => {
    const q = search.trim().toLowerCase();
    return conversations
      .filter((c) => filter === "all" || c.channels.includes(filter))
      .filter((c) => {
        if (!q) return true;
        const name = leadSummaries[c.leadId]?.name || "";
        return String(c.leadId).includes(q) || name.toLowerCase().includes(q);
      })
      .map((c) => ({ id: c.leadId, conversation: c }));
  }, [conversations, filter, search, leadSummaries]);

  const rows = useMemo(() => allRows.slice(0, page * PAGE_SIZE), [allRows, page]);

  const filterOptions = FILTERS.map((f) => ({
    ...f,
    count: f.value === "all" ? conversations.length : conversations.filter((c) => c.channels.includes(f.value)).length,
  }));

  const columns = [
    {
      key: "name",
      label: "Contact",
      render: (r) => {
        const summary = leadSummaries[r.conversation.leadId];
        const name = summary?.name || `Lead #${r.conversation.leadId}`;
        const initials = summary?.name
          ? summary.name.split(" ").map((w) => w[0]).slice(0, 2).join("").toUpperCase()
          : String(r.conversation.leadId).slice(0, 2);
        return (
          <div className="flex items-center gap-3">
            <Avatar className="h-8 w-8">
              <AvatarFallback className="bg-primary/10 text-[11px] font-semibold text-primary">{initials}</AvatarFallback>
            </Avatar>
            <div className="min-w-0">
              <div className="truncate text-sm font-semibold">{name}</div>
              <div className="truncate text-xs text-muted-foreground">{summary?.email || summary?.phone || "—"}</div>
            </div>
          </div>
        );
      },
    },
    {
      key: "channels",
      label: "Channels",
      render: (r) => (
        <div className="flex flex-wrap gap-1">
          {r.conversation.channels.length === 0 ? <ChannelBadge channel="system" /> : r.conversation.channels.map((ch) => <ChannelBadge key={ch} channel={ch} />)}
        </div>
      ),
    },
    {
      key: "lastMessage",
      label: "Last Message",
      render: (r) => <span className="line-clamp-1 max-w-[240px] text-xs text-muted-foreground">{previewFor(r.conversation.latestEvent)}</span>,
    },
    {
      key: "lastActivity",
      label: "Last Activity",
      render: (r) => <span className="whitespace-nowrap text-xs text-muted-foreground">{formatRelative(r.conversation.lastActivityAt)}</span>,
    },
    {
      key: "journey",
      label: "Journey Status",
      render: (r) => {
        const instance = instancesByLead[r.conversation.leadId];
        if (!instance) return <span className="text-xs text-muted-foreground">—</span>;
        const journey = journeyMap[instance.journey_id];
        return (
          <span className="whitespace-nowrap text-xs">
            {journey?.name || "Journey"} <span className="text-muted-foreground">· {instance.status}</span>
          </span>
        );
      },
    },
    {
      key: "messageCount",
      label: "Messages",
      render: (r) => <span className="font-mono text-xs">{r.conversation.events.length}</span>,
    },
  ];

  return (
    <div data-testid="page-contacts">
      <PageHeader
        title="Contacts"
        description="Every lead with communication activity — click a row to open the conversation."
      />

      <div className="space-y-4 px-4 py-6 md:px-8">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <SearchBar value={search} onChange={setSearch} placeholder="Search by name or lead ID…" className="w-full sm:max-w-sm" testId="contacts-search" />
          <FilterBar options={filterOptions} value={filter} onChange={setFilter} testId="contacts-filter" />
        </div>

        {loading && conversations.length === 0 ? (
          <LoadingSkeleton rows={6} />
        ) : rows.length === 0 ? (
          <EmptyState icon={Users} title="No contacts yet" description="Contacts appear here once a lead has any communication activity (WhatsApp, email, or automation)." />
        ) : (
          <>
            <DataTable
              columns={columns}
              rows={rows}
              onRowClick={(row) => navigate(`/conversations?lead=${row.conversation.leadId}`)}
              testId="contacts-table"
            />
            {allRows.length > rows.length && (
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span>Showing {rows.length} of {allRows.length}</span>
                <Button variant="outline" size="sm" className="h-7 text-xs" onClick={() => setPage((p) => p + 1)}>
                  Show more
                </Button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

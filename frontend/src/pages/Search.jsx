import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import PageHeader from "@/components/PageHeader";
import SearchBar from "@/components/SearchBar";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import EmptyState from "@/components/EmptyState";
import { useConversations, useLeadSummaries, previewFor } from "@/modules/inbox";
import { journeyService } from "@/services/journeys";
import { templateService } from "@/services/templates";
import { whatsappTemplateService } from "@/services/whatsappTemplates";
import { formatDateTimeWithRelative, resolveEventTimestamp } from "@/lib/dateFormat";
import { Search, MessageSquare, Users, Workflow, FileText, Megaphone } from "lucide-react";

const PAGE_SIZE = 8;

/**
 * Real, live search across everything that has a queryable API:
 * conversations + individual messages (communication_events, via the
 * existing useConversations hook — same data Inbox uses), contacts (lead
 * summaries already cached for visible conversations), journeys, and
 * templates (generic + WhatsApp). Reuses existing list queries client-side
 * — no new backend endpoint (a real cross-entity search API would need one,
 * flagged in the Phase 3 report rather than built here).
 *
 * Company search and full contact search (by phone/email across ALL
 * leads, not just ones with existing conversations) are NOT possible —
 * JAWIS exposes no search endpoint, only single-lead-by-id lookup (see
 * Phase 2 report). Campaign search is empty — no campaign data exists
 * (Phase 3 report: the Campaign/Workspace models are broken scaffolding).
 */
export default function SearchPage() {
  const [params, setParams] = useSearchParams();
  const [query, setQuery] = useState(params.get("q") || "");
  const [pages, setPages] = useState({});

  const { conversations } = useConversations();
  const leadIds = useMemo(() => conversations.map((c) => c.leadId), [conversations]);
  const leadSummaries = useLeadSummaries(leadIds);

  const [journeys, setJourneys] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [waTemplates, setWaTemplates] = useState([]);

  useEffect(() => {
    journeyService.list({ limit: 200 }).then(setJourneys).catch(() => setJourneys([]));
    templateService.list({ limit: 200 }).then(setTemplates).catch(() => setTemplates([]));
    whatsappTemplateService.list().then(setWaTemplates).catch(() => setWaTemplates([]));
  }, []);

  const q = query.toLowerCase().trim();

  const results = useMemo(() => {
    if (!q) return { conversations: [], messages: [], contacts: [], journeys: [], templates: [] };

    const matchedConversations = conversations.filter((c) => {
      const name = leadSummaries[c.leadId]?.name || "";
      const hay = `${c.leadId} ${name} ${leadSummaries[c.leadId]?.email || ""} ${leadSummaries[c.leadId]?.phone || ""}`.toLowerCase();
      return hay.includes(q) || c.events.some((e) => `${e.payload?.subject || ""} ${e.payload?.body || ""}`.toLowerCase().includes(q));
    });

    const messages = conversations
      .flatMap((c) => c.events.map((e) => ({ ...e, leadId: c.leadId })))
      .filter((e) => `${e.payload?.subject || ""} ${e.payload?.body || ""} ${e.event_type}`.toLowerCase().includes(q))
      .sort((a, b) => new Date(b.occurred_at) - new Date(a.occurred_at));

    const contacts = conversations.filter((c) => {
      const s = leadSummaries[c.leadId];
      if (!s) return String(c.leadId).includes(q);
      return `${s.name} ${s.email || ""} ${s.phone || ""} ${c.leadId}`.toLowerCase().includes(q);
    });

    const matchedJourneys = journeys.filter((j) => `${j.name} ${j.description || ""}`.toLowerCase().includes(q));

    const matchedTemplates = [
      ...templates.map((t) => ({ ...t, kind: "generic" })),
      ...waTemplates.map((t) => ({ ...t, name: t.template_name, kind: "whatsapp" })),
    ].filter((t) => `${t.name} ${t.content || t.body || ""}`.toLowerCase().includes(q));

    return { conversations: matchedConversations, messages, contacts, journeys: matchedJourneys, templates: matchedTemplates };
  }, [q, conversations, leadSummaries, journeys, templates, waTemplates]);

  const total = Object.values(results).reduce((acc, arr) => acc + arr.length, 0);

  const update = (v) => {
    setQuery(v);
    setPages({});
    setParams(v ? { q: v } : {});
  };

  const pageFor = (key) => pages[key] || 1;
  const showMore = (key) => setPages((p) => ({ ...p, [key]: (p[key] || 1) + 1 }));

  return (
    <div data-testid="page-search">
      <PageHeader
        title="Search"
        description={q ? `${total} result${total === 1 ? "" : "s"} for "${q}"` : "Search across conversations, messages, contacts, journeys and templates."}
      />

      <div className="space-y-5 px-4 py-6 md:px-8">
        <SearchBar
          value={query}
          onChange={update}
          placeholder="Search conversations, messages, contacts, journeys, templates…"
          className="max-w-2xl"
          testId="global-search-input"
        />

        {!q ? (
          <EmptyState icon={Search} title="Start typing to search" description="Company and campaign search aren't available yet — see the Phase 3 report." />
        ) : total === 0 ? (
          <EmptyState icon={Search} title={`No matches for "${q}"`} description="Try a different keyword." />
        ) : (
          <Tabs defaultValue="all" className="w-full">
            <TabsList className="mb-4 flex w-full justify-start overflow-x-auto scrollbar-thin">
              <TabsTrigger value="all" className="text-xs">All <Count n={total} /></TabsTrigger>
              <TabsTrigger value="conversations" className="text-xs">Conversations <Count n={results.conversations.length} /></TabsTrigger>
              <TabsTrigger value="messages" className="text-xs">Messages <Count n={results.messages.length} /></TabsTrigger>
              <TabsTrigger value="contacts" className="text-xs">Contacts <Count n={results.contacts.length} /></TabsTrigger>
              <TabsTrigger value="journeys" className="text-xs">Journeys <Count n={results.journeys.length} /></TabsTrigger>
              <TabsTrigger value="templates" className="text-xs">Templates <Count n={results.templates.length} /></TabsTrigger>
            </TabsList>

            <TabsContent value="all" className="space-y-5">
              {results.contacts.length > 0 && <Section icon={Users} title="Contacts" to="/contacts">{paginate(results.contacts, 1, PAGE_SIZE).map((c) => <ContactRow key={c.leadId} c={c} summary={leadSummaries[c.leadId]} />)}</Section>}
              {results.conversations.length > 0 && <Section icon={MessageSquare} title="Conversations" to="/conversations">{paginate(results.conversations, 1, PAGE_SIZE).map((c) => <ConvRow key={c.leadId} c={c} summary={leadSummaries[c.leadId]} />)}</Section>}
              {results.journeys.length > 0 && <Section icon={Workflow} title="Journeys" to="/journeys">{paginate(results.journeys, 1, PAGE_SIZE).map((j) => <JourneyRow key={j.id} j={j} />)}</Section>}
              {results.templates.length > 0 && <Section icon={FileText} title="Templates" to="/templates">{paginate(results.templates, 1, PAGE_SIZE).map((t) => <TemplateRow key={t.id} t={t} />)}</Section>}
              <EmptyState icon={Megaphone} title="Campaigns not searchable" description="No campaign engine exists yet — see the Phase 3 report." className="border-none bg-transparent p-4" />
            </TabsContent>

            <TabsContent value="conversations" className="space-y-2">
              {paginate(results.conversations, pageFor("conversations"), PAGE_SIZE).map((c) => <ConvRow key={c.leadId} c={c} summary={leadSummaries[c.leadId]} />)}
              {results.conversations.length > pageFor("conversations") * PAGE_SIZE && <MoreButton onClick={() => showMore("conversations")} />}
            </TabsContent>
            <TabsContent value="messages" className="space-y-2">
              {paginate(results.messages, pageFor("messages"), PAGE_SIZE).map((e) => <MessageRow key={e.id} e={e} />)}
              {results.messages.length > pageFor("messages") * PAGE_SIZE && <MoreButton onClick={() => showMore("messages")} />}
            </TabsContent>
            <TabsContent value="contacts" className="space-y-2">
              {paginate(results.contacts, pageFor("contacts"), PAGE_SIZE).map((c) => <ContactRow key={c.leadId} c={c} summary={leadSummaries[c.leadId]} />)}
              {results.contacts.length > pageFor("contacts") * PAGE_SIZE && <MoreButton onClick={() => showMore("contacts")} />}
            </TabsContent>
            <TabsContent value="journeys" className="space-y-2">
              {paginate(results.journeys, pageFor("journeys"), PAGE_SIZE).map((j) => <JourneyRow key={j.id} j={j} />)}
              {results.journeys.length > pageFor("journeys") * PAGE_SIZE && <MoreButton onClick={() => showMore("journeys")} />}
            </TabsContent>
            <TabsContent value="templates" className="space-y-2">
              {paginate(results.templates, pageFor("templates"), PAGE_SIZE).map((t) => <TemplateRow key={t.id} t={t} />)}
              {results.templates.length > pageFor("templates") * PAGE_SIZE && <MoreButton onClick={() => showMore("templates")} />}
            </TabsContent>
          </Tabs>
        )}
      </div>
    </div>
  );
}

function paginate(arr, page, size) {
  return arr.slice(0, page * size);
}

function Count({ n }) {
  return <span className="ml-1.5 rounded bg-secondary px-1 text-[10px] font-semibold">{n}</span>;
}

function MoreButton({ onClick }) {
  return <Button variant="outline" size="sm" className="h-7 text-xs" onClick={onClick}>Show more</Button>;
}

function Section({ icon: Icon, title, to, children }) {
  return (
    <Card className="rounded-xl border-border bg-card p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon className="h-4 w-4 text-muted-foreground" />
          <h3 className="text-sm font-bold">{title}</h3>
        </div>
        <Link to={to} className="text-xs text-primary hover:underline">View all</Link>
      </div>
      <div className="-mx-2 divide-y divide-border">{children}</div>
    </Card>
  );
}

function ConvRow({ c, summary }) {
  return (
    <Link to={`/conversations?lead=${c.leadId}`} className="flex items-center gap-3 px-2 py-2.5 hover:bg-secondary/50">
      <Avatar className="h-8 w-8"><AvatarFallback className="bg-primary/10 text-[11px] font-semibold text-primary">{String(c.leadId).slice(0, 2)}</AvatarFallback></Avatar>
      <div className="min-w-0 flex-1">
        <div className="truncate text-sm font-semibold">{summary?.name || `Lead #${c.leadId}`}</div>
        <div className="truncate text-xs text-muted-foreground">{previewFor(c.latestEvent)}</div>
      </div>
      <span className="shrink-0 text-[11px] text-muted-foreground">{formatDateTimeWithRelative(c.lastActivityAt)}</span>
    </Link>
  );
}

function MessageRow({ e }) {
  return (
    <Link to={`/conversations?lead=${e.leadId}`} className="flex items-center gap-3 px-2 py-2.5 hover:bg-secondary/50">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-secondary"><MessageSquare className="h-3.5 w-3.5" /></div>
      <div className="min-w-0 flex-1">
        <div className="truncate text-sm font-semibold">Lead #{e.leadId} · {e.event_type.replace(/_/g, " ")}</div>
        <div className="truncate text-xs text-muted-foreground">{e.payload?.body || e.payload?.subject || "—"}</div>
      </div>
      <span className="shrink-0 text-[11px] text-muted-foreground">{formatDateTimeWithRelative(resolveEventTimestamp(e))}</span>
    </Link>
  );
}

function ContactRow({ c, summary }) {
  return (
    <Link to={`/conversations?lead=${c.leadId}`} className="flex items-center gap-3 px-2 py-2.5 hover:bg-secondary/50">
      <Avatar className="h-8 w-8"><AvatarFallback className="bg-primary/10 text-[11px] font-semibold text-primary">{String(c.leadId).slice(0, 2)}</AvatarFallback></Avatar>
      <div className="min-w-0 flex-1">
        <div className="truncate text-sm font-semibold">{summary?.name || `Lead #${c.leadId}`}</div>
        <div className="truncate text-xs text-muted-foreground">{summary?.email || summary?.phone || "—"}</div>
      </div>
    </Link>
  );
}

function JourneyRow({ j }) {
  return (
    <Link to="/journeys" className="flex items-center gap-3 px-2 py-2.5 hover:bg-secondary/50">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-secondary"><Workflow className="h-3.5 w-3.5" /></div>
      <div className="min-w-0 flex-1">
        <div className="truncate text-sm font-semibold">{j.name}</div>
        <div className="truncate text-xs text-muted-foreground">{j.status}</div>
      </div>
    </Link>
  );
}

function TemplateRow({ t }) {
  return (
    <Link to={t.kind === "whatsapp" ? "/templates/whatsapp" : "/templates"} className="flex items-center gap-3 px-2 py-2.5 hover:bg-secondary/50">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-secondary"><FileText className="h-3.5 w-3.5" /></div>
      <div className="min-w-0 flex-1">
        <div className="truncate text-sm font-semibold">{t.name}</div>
        <div className="truncate text-xs text-muted-foreground">{t.channel || "whatsapp"}</div>
      </div>
    </Link>
  );
}

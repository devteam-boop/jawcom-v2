import { useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import PageHeader from "@/components/PageHeader";
import SearchBar from "@/components/SearchBar";
import { Card } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import StatusBadge from "@/components/StatusBadge";
import EmptyState from "@/components/EmptyState";
import { CONVERSATIONS, CUSTOMERS, CAMPAIGNS } from "@/dummy-data";
import { COMPANIES } from "@/dummy-data/companies";
import { KNOWLEDGE_DOCS } from "@/dummy-data/knowledge";
import { Search, MessageSquare, Users, Building2, Megaphone, BookOpen } from "lucide-react";

export default function SearchPage() {
  const [params, setParams] = useSearchParams();
  const initial = params.get("q") || "";
  const [query, setQuery] = useState(initial);

  const q = query.toLowerCase().trim();

  const results = useMemo(() => {
    if (!q) {
      return { conversations: [], customers: [], companies: [], campaigns: [], knowledge: [] };
    }
    return {
      conversations: CONVERSATIONS.filter((c) => `${c.customer} ${c.company} ${c.preview}`.toLowerCase().includes(q)).slice(0, 8),
      customers: CUSTOMERS.filter((c) => `${c.name} ${c.email} ${c.company}`.toLowerCase().includes(q)).slice(0, 8),
      companies: COMPANIES.filter((c) => `${c.name} ${c.industry} ${c.primary}`.toLowerCase().includes(q)).slice(0, 8),
      campaigns: CAMPAIGNS.filter((c) => `${c.name} ${c.channel}`.toLowerCase().includes(q)).slice(0, 8),
      knowledge: KNOWLEDGE_DOCS.filter((d) => `${d.title} ${d.source} ${d.type}`.toLowerCase().includes(q)).slice(0, 8),
    };
  }, [q]);

  const total = Object.values(results).reduce((acc, arr) => acc + arr.length, 0);

  const update = (v) => {
    setQuery(v);
    setParams(v ? { q: v } : {});
  };

  return (
    <div data-testid="page-search">
      <PageHeader
        title="Search"
        description={q ? `${total} result${total === 1 ? "" : "s"} for "${q}"` : "Search across your entire workspace."}
      />

      <div className="space-y-5 px-4 py-6 md:px-8">
        <SearchBar
          value={query}
          onChange={update}
          placeholder="Search customers, companies, conversations, campaigns, docs…"
          className="max-w-2xl"
          testId="global-search-input"
        />

        {!q ? (
          <EmptyState
            icon={Search}
            title="Start typing to search"
            description="JawCom searches across people, accounts, conversations, campaigns and your knowledge base."
          />
        ) : total === 0 ? (
          <EmptyState
            icon={Search}
            title={`No matches for "${q}"`}
            description="Try a different keyword or check your filters."
          />
        ) : (
          <Tabs defaultValue="all" className="w-full">
            <TabsList className="mb-4 flex w-full justify-start overflow-x-auto scrollbar-thin">
              <TabsTrigger value="all" className="text-xs">All <span className="ml-1.5 rounded bg-secondary px-1 text-[10px] font-semibold">{total}</span></TabsTrigger>
              <TabsTrigger value="conversations" className="text-xs">Conv. <span className="ml-1.5 rounded bg-secondary px-1 text-[10px] font-semibold">{results.conversations.length}</span></TabsTrigger>
              <TabsTrigger value="customers" className="text-xs">People <span className="ml-1.5 rounded bg-secondary px-1 text-[10px] font-semibold">{results.customers.length}</span></TabsTrigger>
              <TabsTrigger value="companies" className="text-xs">Companies <span className="ml-1.5 rounded bg-secondary px-1 text-[10px] font-semibold">{results.companies.length}</span></TabsTrigger>
              <TabsTrigger value="campaigns" className="text-xs">Camp. <span className="ml-1.5 rounded bg-secondary px-1 text-[10px] font-semibold">{results.campaigns.length}</span></TabsTrigger>
              <TabsTrigger value="knowledge" className="text-xs">Docs <span className="ml-1.5 rounded bg-secondary px-1 text-[10px] font-semibold">{results.knowledge.length}</span></TabsTrigger>
            </TabsList>

            <TabsContent value="all" className="space-y-5">
              {results.conversations.length > 0 && <Section icon={MessageSquare} title="Conversations" to="/conversations">{results.conversations.map((c) => <ConvRow key={c.id} c={c} />)}</Section>}
              {results.customers.length > 0 && <Section icon={Users} title="People" to="/contacts">{results.customers.map((c) => <PersonRow key={c.id} c={c} />)}</Section>}
              {results.companies.length > 0 && <Section icon={Building2} title="Companies" to="/contacts">{results.companies.map((c) => <CompanyRow key={c.id} c={c} />)}</Section>}
              {results.campaigns.length > 0 && <Section icon={Megaphone} title="Campaigns" to="/campaigns">{results.campaigns.map((c) => <CampaignRow key={c.id} c={c} />)}</Section>}
              {results.knowledge.length > 0 && <Section icon={BookOpen} title="Knowledge" to="/knowledge">{results.knowledge.map((d) => <DocRow key={d.id} d={d} />)}</Section>}
            </TabsContent>

            <TabsContent value="conversations">{results.conversations.map((c) => <ConvRow key={c.id} c={c} />)}</TabsContent>
            <TabsContent value="customers">{results.customers.map((c) => <PersonRow key={c.id} c={c} />)}</TabsContent>
            <TabsContent value="companies">{results.companies.map((c) => <CompanyRow key={c.id} c={c} />)}</TabsContent>
            <TabsContent value="campaigns">{results.campaigns.map((c) => <CampaignRow key={c.id} c={c} />)}</TabsContent>
            <TabsContent value="knowledge">{results.knowledge.map((d) => <DocRow key={d.id} d={d} />)}</TabsContent>
          </Tabs>
        )}
      </div>
    </div>
  );
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

function ConvRow({ c }) {
  return (
    <div className="flex items-center gap-3 px-2 py-2.5">
      <Avatar className="h-8 w-8">
        <AvatarFallback className="bg-primary/10 text-[11px] font-semibold text-primary">{c.initials}</AvatarFallback>
      </Avatar>
      <div className="min-w-0 flex-1">
        <div className="truncate text-sm font-semibold">{c.customer} · {c.company}</div>
        <div className="truncate text-xs text-muted-foreground">{c.preview}</div>
      </div>
      <StatusBadge status={c.status} />
    </div>
  );
}

function PersonRow({ c }) {
  return (
    <div className="flex items-center gap-3 px-2 py-2.5">
      <Avatar className="h-8 w-8">
        <AvatarFallback className="bg-primary/10 text-[11px] font-semibold text-primary">{c.initials}</AvatarFallback>
      </Avatar>
      <div className="min-w-0 flex-1">
        <div className="truncate text-sm font-semibold">{c.name}</div>
        <div className="truncate text-xs text-muted-foreground">{c.email}</div>
      </div>
      <StatusBadge status={c.status} />
    </div>
  );
}

function CompanyRow({ c }) {
  return (
    <div className="flex items-center gap-3 px-2 py-2.5">
      <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary/10 text-[11px] font-bold text-primary">{c.logo}</div>
      <div className="min-w-0 flex-1">
        <div className="truncate text-sm font-semibold">{c.name}</div>
        <div className="truncate text-xs text-muted-foreground">{c.industry} · {c.primary}</div>
      </div>
      <StatusBadge status={c.stage} />
    </div>
  );
}

function CampaignRow({ c }) {
  return (
    <div className="flex items-center gap-3 px-2 py-2.5">
      <div className="flex h-8 w-8 items-center justify-center rounded-md bg-secondary"><Megaphone className="h-3.5 w-3.5" /></div>
      <div className="min-w-0 flex-1">
        <div className="truncate text-sm font-semibold">{c.name}</div>
        <div className="truncate text-xs text-muted-foreground">{c.channel} · {c.audience.toLocaleString()} contacts</div>
      </div>
      <StatusBadge status={c.status} />
    </div>
  );
}

function DocRow({ d }) {
  return (
    <div className="flex items-center gap-3 px-2 py-2.5">
      <div className="flex h-8 w-8 items-center justify-center rounded-md bg-secondary"><BookOpen className="h-3.5 w-3.5" /></div>
      <div className="min-w-0 flex-1">
        <div className="truncate text-sm font-semibold">{d.title}</div>
        <div className="truncate text-xs text-muted-foreground">{d.type} · {d.source}</div>
      </div>
      {d.aiReady && <span className="rounded bg-primary/10 px-1.5 py-0.5 text-[10px] font-semibold text-primary">AI Ready</span>}
    </div>
  );
}

import { useMemo, useState } from "react";
import SearchBar from "@/components/SearchBar";
import FilterBar from "@/components/FilterBar";
import StatusBadge from "@/components/StatusBadge";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import { CONVERSATIONS, CONVERSATION_THREAD, QUICK_REPLIES } from "@/dummy-data";
import {
  Paperclip,
  Smile,
  Mic,
  Send,
  Phone,
  Video,
  MoreHorizontal,
  Sparkles,
  Tag,
  StickyNote,
  Mail,
  Instagram,
  MessageCircle,
  Facebook,
  MessageSquare,
  Lock,
  Pause,
  Zap,
  Undo2,
} from "lucide-react";

const channelIcon = {
  WhatsApp: MessageCircle,
  Email: Mail,
  Instagram: Instagram,
  Facebook: Facebook,
  SMS: MessageSquare,
};

const FILTERS = [
  { label: "Unread", value: "Unread" },
  { label: "Open", value: "Open" },
  { label: "Closed", value: "Closed" },
  { label: "Assigned", value: "Assigned" },
  { label: "All", value: "all" },
];

export default function Inbox() {
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [selectedId, setSelectedId] = useState(CONVERSATIONS[0].id);

  const filtered = useMemo(() => {
    return CONVERSATIONS.filter((c) => {
      if (filter !== "all" && c.status !== filter) return false;
      if (search && !`${c.customer} ${c.company} ${c.preview}`.toLowerCase().includes(search.toLowerCase())) return false;
      return true;
    });
  }, [filter, search]);

  const selected = CONVERSATIONS.find((c) => c.id === selectedId) || CONVERSATIONS[0];

  const filterOptions = FILTERS.map((f) => ({
    ...f,
    count: f.value === "all" ? CONVERSATIONS.length : CONVERSATIONS.filter((c) => c.status === f.value).length,
  }));

  return (
    <div className="flex h-full min-h-0 flex-col lg:flex-row" data-testid="page-inbox">
      {/* LEFT: Conversation list */}
      <aside className="flex w-full shrink-0 flex-col border-b border-border lg:w-[340px] lg:border-b-0 lg:border-r" data-testid="conversation-list">
        <div className="flex flex-col gap-3 border-b border-border p-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold">Inbox</h2>
            <Button variant="ghost" size="sm" className="text-xs" data-testid="inbox-sort">
              Newest
            </Button>
          </div>
          <SearchBar value={search} onChange={setSearch} placeholder="Search conversations…" testId="conversations-search" />
          <FilterBar options={filterOptions} value={filter} onChange={setFilter} testId="conversations-filter" />
        </div>
        <div className="flex-1 overflow-y-auto scrollbar-thin">
          {filtered.map((c) => {
            const Icon = channelIcon[c.channel] || MessageCircle;
            const active = c.id === selectedId;
            return (
              <button
                key={c.id}
                onClick={() => setSelectedId(c.id)}
                className={cn(
                  "flex w-full gap-3 border-b border-border/60 p-4 text-left transition-colors hover:bg-secondary/50",
                  active && "bg-accent"
                )}
                data-testid={`conv-item-${c.id}`}
              >
                <div className="relative shrink-0">
                  <Avatar className="h-10 w-10">
                    <AvatarFallback className="bg-primary/10 text-xs font-semibold text-primary">
                      {c.initials}
                    </AvatarFallback>
                  </Avatar>
                  <span className="absolute -bottom-0.5 -right-0.5 flex h-4 w-4 items-center justify-center rounded-full border-2 border-card bg-card">
                    <Icon className="h-2.5 w-2.5 text-muted-foreground" />
                  </span>
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <span className="truncate text-sm font-semibold">{c.customer}</span>
                    <span className="shrink-0 text-[11px] text-muted-foreground">{c.time}</span>
                  </div>
                  <p className="mt-0.5 truncate text-xs text-muted-foreground">{c.company}</p>
                  <p className={cn("mt-1 line-clamp-1 text-xs", c.unread > 0 ? "font-medium text-foreground" : "text-muted-foreground")}>
                    {c.preview}
                  </p>
                  <div className="mt-2 flex items-center gap-1.5">
                    <StatusBadge status={c.status} />
                    {c.unread > 0 && (
                      <span className="inline-flex h-4 min-w-4 items-center justify-center rounded-full bg-primary px-1 text-[10px] font-bold text-primary-foreground">
                        {c.unread}
                      </span>
                    )}
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </aside>

      {/* CENTER: Chat thread */}
      <section className="flex min-w-0 flex-1 flex-col" data-testid="conversation-thread">
        {/* Thread header */}
        <div className="flex items-center justify-between border-b border-border p-4">
          <div className="flex items-center gap-3">
            <Avatar className="h-10 w-10">
              <AvatarFallback className="bg-primary/10 text-xs font-semibold text-primary">
                {selected.initials}
              </AvatarFallback>
            </Avatar>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-bold">{selected.customer}</h3>
                <span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-500" />
                <span className="text-xs text-muted-foreground">Online · {selected.channel}</span>
              </div>
              <p className="text-xs text-muted-foreground">{selected.company}</p>
            </div>
          </div>
          <div className="flex items-center gap-1">
            <Button variant="ghost" size="icon" className="h-8 w-8" data-testid="thread-call">
              <Phone className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="icon" className="h-8 w-8" data-testid="thread-video">
              <Video className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="icon" className="h-8 w-8" data-testid="thread-more">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 space-y-4 overflow-y-auto scrollbar-thin bg-secondary/20 p-6">
          {CONVERSATION_THREAD.map((m) => {
            if (m.from === "ai") {
              return (
                <div key={m.id} className="mx-auto max-w-xl rounded-xl border border-primary/30 bg-primary/5 p-3" data-testid={`msg-${m.id}`}>
                  <div className="mb-1 flex items-center gap-1.5 text-xs font-semibold text-primary">
                    <Sparkles className="h-3 w-3" />
                    AI Assistant · suggested reply
                  </div>
                  <p className="text-sm">{m.text}</p>
                  <div className="mt-2 flex gap-1.5">
                    <Button size="sm" className="h-7 text-xs" data-testid="ai-use-suggestion">Use</Button>
                    <Button size="sm" variant="ghost" className="h-7 text-xs">Edit</Button>
                  </div>
                </div>
              );
            }
            const isAgent = m.from === "agent";
            return (
              <div key={m.id} className={cn("flex gap-2", isAgent ? "justify-end" : "justify-start")} data-testid={`msg-${m.id}`}>
                {!isAgent && (
                  <Avatar className="h-7 w-7 shrink-0">
                    <AvatarFallback className="bg-secondary text-[10px] font-semibold">
                      {selected.initials}
                    </AvatarFallback>
                  </Avatar>
                )}
                <div className={cn("max-w-[70%]", isAgent && "text-right")}>
                  <div
                    className={cn(
                      "rounded-2xl px-4 py-2.5 text-sm shadow-sm",
                      isAgent
                        ? "rounded-br-md bg-primary text-primary-foreground"
                        : "rounded-bl-md border border-border bg-card"
                    )}
                  >
                    {m.text}
                  </div>
                  {m.isAutoSent && (
                    <div
                      className={cn(
                        "mt-1 inline-flex items-center gap-1 rounded-md bg-secondary px-1.5 py-0.5 text-[11px] font-medium text-muted-foreground",
                        isAgent && "ml-auto"
                      )}
                      data-testid={`auto-sent-${m.id}`}
                    >
                      <Zap className="h-2.5 w-2.5" />
                      <span>{m.journey}</span>
                      <span className="text-muted-foreground/60">·</span>
                      <span>auto-sent</span>
                    </div>
                  )}
                  <span className="mt-1 block text-[10px] text-muted-foreground">{m.time}</span>
                </div>
              </div>
            );
          })}
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span className="flex gap-0.5">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-muted-foreground" />
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-muted-foreground [animation-delay:150ms]" />
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-muted-foreground [animation-delay:300ms]" />
            </span>
            <span>{selected.customer} is typing…</span>
          </div>
        </div>

        {/* Quick replies */}
        <div className="flex flex-wrap gap-1.5 border-t border-border bg-background px-4 pt-3">
          {QUICK_REPLIES.map((q, i) => (
            <button
              key={i}
              className="rounded-full border border-border bg-secondary/50 px-3 py-1 text-xs text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
              data-testid={`quick-reply-${i}`}
            >
              {q}
            </button>
          ))}
        </div>

        {/* Composer */}
        <div className="border-t border-border bg-background p-4">
          <div className="rounded-xl border border-border bg-card focus-within:border-primary/40 focus-within:ring-2 focus-within:ring-primary/10">
            <Textarea
              placeholder={`Reply to ${selected.customer} on ${selected.channel}…`}
              rows={2}
              className="resize-none border-0 bg-transparent text-sm focus-visible:ring-0 focus-visible:ring-offset-0"
              data-testid="composer-input"
            />
            <div className="flex items-center justify-between border-t border-border/60 px-2 py-1.5">
              <div className="flex items-center gap-0.5">
                <Button variant="ghost" size="icon" className="h-7 w-7" data-testid="composer-attach">
                  <Paperclip className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="icon" className="h-7 w-7" data-testid="composer-emoji">
                  <Smile className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="icon" className="h-7 w-7" data-testid="composer-voice">
                  <Mic className="h-4 w-4" />
                </Button>
                <Separator orientation="vertical" className="mx-1 h-4" />
                <Button variant="ghost" size="sm" className="h-7 px-2 text-xs" data-testid="composer-ai">
                  <Sparkles className="mr-1 h-3 w-3 text-primary" />
                  AI draft
                </Button>
              </div>
              <Button size="sm" className="h-7" data-testid="composer-send">
                <Send className="mr-1 h-3 w-3" /> Send
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* RIGHT: Customer profile */}
      <aside className="hidden w-[300px] shrink-0 flex-col border-l border-border bg-card/30 xl:flex" data-testid="conversation-profile">
        <div className="p-5 text-center">
          <Avatar className="mx-auto h-16 w-16">
            <AvatarFallback className="bg-primary/10 text-lg font-semibold text-primary">
              {selected.initials}
            </AvatarFallback>
          </Avatar>
          <h3 className="mt-3 text-base font-bold">{selected.customer}</h3>
          <p className="text-xs text-muted-foreground">{selected.company}</p>
          <div className="mt-3 flex justify-center gap-1.5">
            <Button variant="outline" size="sm" className="h-7 text-xs">
              <Phone className="mr-1 h-3 w-3" /> Call
            </Button>
            <Button variant="outline" size="sm" className="h-7 text-xs">
              <Mail className="mr-1 h-3 w-3" /> Email
            </Button>
          </div>
        </div>
        <Separator />

        <div className="space-y-5 overflow-y-auto scrollbar-thin p-5 text-sm" data-testid="context-panel">
          {/* JAWIS — locked CRM context */}
          <div data-testid="jawis-section">
            <div className="mb-3 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
              <Lock className="h-3 w-3 text-muted-foreground/70" />
              <span>JAWIS</span>
            </div>
            <div className="space-y-2 rounded-lg border border-border bg-card p-3">
              <ContextField label="Company" value={selected.company} />
              <ContextField label="Lead Stage" value={selected.stage} />
              <ContextField label="Owner" value={selected.assignee} />
              <ContextField label="Requirement" value="40 seats" />
              <ContextField label="Deal Value" value="₹6.4L/mo" />
            </div>
          </div>

          {/* Journey */}
          <div data-testid="journey-section">
            <div className="mb-3 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
              Journey
            </div>
            <div className="rounded-lg border border-border bg-card p-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold">Visit Reminder</span>
                <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-600 dark:text-emerald-400">
                  <span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-500" />
                  Active
                </span>
              </div>
              <div className="mt-2 flex items-center gap-3 text-[11px] text-muted-foreground">
                <span><span className="font-mono font-semibold text-foreground">2</span> sent</span>
                <span>·</span>
                <span><span className="font-mono font-semibold text-foreground">1</span> reply</span>
              </div>
            </div>
          </div>

          {/* Journey controls */}
          <div className="flex flex-col gap-1.5" data-testid="journey-controls">
            <Button variant="outline" size="sm" className="h-8 justify-start text-xs" data-testid="journey-pause">
              <Pause className="mr-2 h-3 w-3" /> Pause
            </Button>
            <Button variant="outline" size="sm" className="h-8 justify-start text-xs" data-testid="journey-override">
              <Undo2 className="mr-2 h-3 w-3" /> Override
            </Button>
            <Button variant="outline" size="sm" className="h-8 justify-start text-xs" data-testid="journey-ai-toggle">
              <Sparkles className="mr-2 h-3 w-3" /> AI On/Off
            </Button>
          </div>
        </div>
      </aside>
    </div>
  );
}

function ContextField({ label, value }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="text-[11px] text-muted-foreground">{label}</span>
      <span className="truncate text-xs font-medium">{value}</span>
    </div>
  );
}

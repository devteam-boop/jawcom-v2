import { useMemo } from "react";
import SearchBar from "@/components/SearchBar";
import FilterBar from "@/components/FilterBar";
import StatusBadge from "@/components/StatusBadge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";
import { MessageCircle, Mail, Instagram, Facebook, MessageSquare } from "lucide-react";

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

export default function ConversationList({ conversations, selectedId, onSelect, search, onSearchChange, filter, onFilterChange }) {
  const filtered = useMemo(() => {
    return conversations.filter((c) => {
      if (filter !== "all" && c.status !== filter) return false;
      if (search && !`${c.customer} ${c.company} ${c.preview}`.toLowerCase().includes(search.toLowerCase())) return false;
      return true;
    });
  }, [conversations, filter, search]);

  const filterOptions = FILTERS.map((f) => ({
    ...f,
    count: f.value === "all" ? conversations.length : conversations.filter((c) => c.status === f.value).length,
  }));

  return (
    <aside className="flex w-full shrink-0 flex-col border-b border-border lg:w-[340px] lg:border-b-0 lg:border-r">
      <div className="flex flex-col gap-3 border-b border-border p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold">Inbox</h2>
        </div>
        <SearchBar value={search} onChange={onSearchChange} placeholder="Search conversations…" testId="conversations-search" />
        <FilterBar options={filterOptions} value={filter} onChange={onFilterChange} testId="conversations-filter" />
      </div>
      <div className="flex-1 overflow-y-auto scrollbar-thin">
        {filtered.map((c) => {
          const Icon = channelIcon[c.channel] || MessageCircle;
          const active = c.id === selectedId;
          return (
            <button
              key={c.id}
              onClick={() => onSelect(c.id)}
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
  );
}

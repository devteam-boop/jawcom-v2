import { useMemo } from "react";
import SearchBar from "@/components/SearchBar";
import FilterBar from "@/components/FilterBar";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";
import ChannelBadge from "./ChannelBadge";
import { previewFor } from "./conversationPreview";
import { isConversationUnread } from "./unreadTracker";

const FILTERS = [
  { label: "All", value: "all" },
  { label: "Unread", value: "unread" },
];

/**
 * One row per lead ("one conversation per lead"). Grouping WhatsApp/Email/
 * Notes/future channels together means each row shows every channel that
 * has activity for that lead as small badges, rather than splitting the
 * list by channel.
 */
export default function ConversationList({ conversations, selectedLeadId, onSelect, search, onSearchChange, filter, onFilterChange }) {
  const filtered = useMemo(() => {
    return conversations.filter((c) => {
      if (filter === "unread" && !isConversationUnread(c.leadId, c.lastActivityAt)) return false;
      if (search && !String(c.leadId).includes(search.trim())) return false;
      return true;
    });
  }, [conversations, filter, search]);

  const unreadCount = useMemo(
    () => conversations.filter((c) => isConversationUnread(c.leadId, c.lastActivityAt)).length,
    [conversations]
  );

  const filterOptions = FILTERS.map((f) => ({
    ...f,
    count: f.value === "all" ? conversations.length : unreadCount,
  }));

  return (
    <aside
      className="flex w-full shrink-0 flex-col border-b border-border lg:w-[360px] lg:border-b-0 lg:border-r"
      data-testid="conversation-list"
    >
      <div className="flex flex-col gap-3 border-b border-border p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold">Inbox</h2>
        </div>
        <SearchBar value={search} onChange={onSearchChange} placeholder="Search by lead ID…" testId="conversations-search" />
        <FilterBar options={filterOptions} value={filter} onChange={onFilterChange} testId="conversations-filter" />
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-thin">
        {filtered.length === 0 ? (
          <div className="p-6 text-center text-sm text-muted-foreground">No conversations found.</div>
        ) : (
          filtered.map((c) => {
            const active = c.leadId === selectedLeadId;
            const unread = isConversationUnread(c.leadId, c.lastActivityAt);
            return (
              <button
                key={c.leadId}
                onClick={() => onSelect(c.leadId)}
                className={cn(
                  "flex w-full gap-3 border-b border-border/60 p-4 text-left transition-colors hover:bg-secondary/50",
                  active && "bg-accent"
                )}
                data-testid={`conv-item-${c.leadId}`}
              >
                <div className="relative shrink-0">
                  <Avatar className="h-10 w-10">
                    <AvatarFallback className="bg-primary/10 text-xs font-semibold text-primary">
                      {String(c.leadId).slice(0, 2)}
                    </AvatarFallback>
                  </Avatar>
                  {unread && (
                    <span
                      className="absolute -right-0.5 -top-0.5 h-2.5 w-2.5 rounded-full border-2 border-card bg-primary"
                      data-testid={`unread-dot-${c.leadId}`}
                      title="Unread (local placeholder — not backend-tracked)"
                    />
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <span className="truncate text-sm font-semibold">Lead #{c.leadId}</span>
                    <span className="shrink-0 text-[11px] text-muted-foreground">
                      {c.lastActivityAt ? new Date(c.lastActivityAt).toLocaleString() : "—"}
                    </span>
                  </div>
                  <p className={cn("mt-1 line-clamp-1 text-xs", unread ? "font-medium text-foreground" : "text-muted-foreground")}>
                    {previewFor(c.latestEvent)}
                  </p>
                  <div className="mt-2 flex flex-wrap items-center gap-1.5">
                    {c.channels.length === 0 ? (
                      <ChannelBadge channel="system" />
                    ) : (
                      c.channels.map((ch) => <ChannelBadge key={ch} channel={ch} />)
                    )}
                  </div>
                </div>
              </button>
            );
          })
        )}
      </div>
    </aside>
  );
}

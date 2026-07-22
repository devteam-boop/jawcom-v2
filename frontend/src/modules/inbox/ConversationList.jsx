import { useMemo } from "react";
import SearchBar from "@/components/SearchBar";
import FilterBar from "@/components/FilterBar";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";
import { formatDateTimeWithRelative, formatTooltip } from "@/lib/dateFormat";
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
export default function ConversationList({ conversations, selectedLeadId, onSelect, search, onSearchChange, filter, onFilterChange, leadSummaries = {} }) {
  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return conversations.filter((c) => {
      if (filter === "unread" && !isConversationUnread(c.leadId, c.lastActivityAt)) return false;
      if (q) {
        const name = leadSummaries[c.leadId]?.name || "";
        if (!String(c.leadId).includes(q) && !name.toLowerCase().includes(q)) return false;
      }
      return true;
    });
  }, [conversations, filter, search, leadSummaries]);

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
            const name = leadSummaries[c.leadId]?.name || `Lead #${c.leadId}`;
            const initials = leadSummaries[c.leadId]?.name
              ? leadSummaries[c.leadId].name.split(" ").map((w) => w[0]).slice(0, 2).join("").toUpperCase()
              : String(c.leadId).slice(0, 2);
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
                      {initials}
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
                    <span className="truncate text-sm font-semibold">{name}</span>
                    <span className="shrink-0 text-[11px] text-muted-foreground" title={formatTooltip(c.lastActivityAt)}>
                      {formatDateTimeWithRelative(c.lastActivityAt)}
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

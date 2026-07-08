import { useState, useMemo } from "react";
import LoadingSkeleton from "@/components/LoadingSkeleton";
import { ConversationList, ConversationThread, useConversations } from "@/modules/inbox";

/**
 * Unified Inbox — one conversation per lead, backed entirely by the
 * existing communication-events API. Reuses CommunicationTimeline (via
 * ConversationThread) for the full history view instead of duplicating it.
 *
 * This replaces the previous dummy-data mockup that lived at this same
 * route/nav slot ("Inbox" -> /conversations) — that mockup rendered fake
 * customers/companies/AI-suggested-replies against a backend endpoint
 * (/api/inbox) that doesn't exist. No real functionality is lost by
 * replacing it; it was never wired to anything.
 */
export default function Conversations() {
  const { conversations, loading } = useConversations();
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");
  const [selectedLeadId, setSelectedLeadId] = useState(null);

  const selected = useMemo(
    () => conversations.find((c) => c.leadId === selectedLeadId) || null,
    [conversations, selectedLeadId]
  );

  if (loading && conversations.length === 0) {
    return (
      <div className="flex h-full min-h-0 flex-col p-6" data-testid="page-conversations">
        <LoadingSkeleton rows={6} />
      </div>
    );
  }

  return (
    <div className="flex h-full min-h-0 flex-col lg:flex-row" data-testid="page-conversations">
      <ConversationList
        conversations={conversations}
        selectedLeadId={selectedLeadId}
        onSelect={setSelectedLeadId}
        search={search}
        onSearchChange={setSearch}
        filter={filter}
        onFilterChange={setFilter}
      />
      <ConversationThread conversation={selected} />
    </div>
  );
}

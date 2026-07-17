import { useState, useMemo, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import LoadingSkeleton from "@/components/LoadingSkeleton";
import { ConversationList, ConversationThread, useConversations, useLeadSummaries } from "@/modules/inbox";

/**
 * Unified Inbox — one conversation per lead, backed entirely by the
 * existing communication-events API. Reuses CommunicationTimeline (via
 * ConversationThread) for the full history view instead of duplicating it.
 *
 * Auto-updates every 10s via useConversations' own polling (no WebSocket
 * infra exists in this backend — polling was the lighter, already-
 * established choice, see Phase 2 report). Supports ?lead=<id> deep-linking
 * so Contacts can open a conversation directly.
 */
export default function Conversations() {
  const { conversations, loading } = useConversations();
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");
  const [selectedLeadId, setSelectedLeadId] = useState(null);
  const [searchParams, setSearchParams] = useSearchParams();

  useEffect(() => {
    const leadParam = searchParams.get("lead");
    if (leadParam) {
      setSelectedLeadId(Number(leadParam));
      setSearchParams({}, { replace: true });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  const leadIds = useMemo(() => conversations.map((c) => c.leadId), [conversations]);
  const leadSummaries = useLeadSummaries(leadIds);

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
        leadSummaries={leadSummaries}
      />
      <ConversationThread conversation={selected} />
    </div>
  );
}

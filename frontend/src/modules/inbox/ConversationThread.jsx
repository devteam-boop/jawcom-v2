import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import EmptyState from "@/components/EmptyState";
import { formatDateTimeWithRelative } from "@/lib/dateFormat";
import { jawisService } from "@/services/jawis";
import { runningInstanceService } from "@/services/runningInstances";
import { journeyService } from "@/services/journeys";
import ChannelBadge from "./ChannelBadge";
import ChatThread from "./ChatThread";
import MessageComposer from "./MessageComposer";
import { markConversationSeen } from "./unreadTracker";
import { MessagesSquare, ExternalLink, Phone, Mail } from "lucide-react";

/**
 * The full thread view: header (real lead identity + journey status),
 * a WhatsApp-Business-style chat rendering of the same communication_events
 * CommunicationTimeline reads (see ChatThread.jsx — the Inbox-specific
 * display; CommunicationTimeline itself is untouched and still used as the
 * technical/debug log in ExecutionDrawer and Lead Activity), and a live
 * composer. Manual sends are merged in optimistically (Phase 2 Task 4)
 * until the next poll brings back the real communication_events row with
 * the same id.
 */
export default function ConversationThread({ conversation }) {
  const leadId = conversation?.leadId;

  const [leadSummary, setLeadSummary] = useState(null);
  const [leadSummaryError, setLeadSummaryError] = useState(false);
  const [currentInstance, setCurrentInstance] = useState(null);
  const [journeyName, setJourneyName] = useState(null);
  const [pending, setPending] = useState([]);

  useEffect(() => {
    setPending([]);
    if (leadId == null) return undefined;
    let active = true;
    setLeadSummary(null);
    setLeadSummaryError(false);
    jawisService
      .getLead(leadId)
      .then((data) => { if (active) setLeadSummary(data); })
      .catch(() => { if (active) setLeadSummaryError(true); });

    runningInstanceService
      .list({ leadId, limit: 5 })
      .then((instances) => {
        if (!active) return;
        const running = instances.find((i) => i.status === "running") || instances[0] || null;
        setCurrentInstance(running);
        if (running?.journey_id) {
          journeyService.get(running.journey_id).then((j) => { if (active) setJourneyName(j.name); }).catch(() => {});
        } else {
          setJourneyName(null);
        }
      })
      .catch(() => { if (active) setCurrentInstance(null); });

    markConversationSeen(leadId);
    return () => { active = false; };
  }, [leadId]);

  // Drop any optimistic entry once the real row (same id) shows up in the
  // next poll's fetched events.
  useEffect(() => {
    if (!conversation) return;
    const realIds = new Set(conversation.events.map((e) => e.id));
    setPending((prev) => prev.filter((p) => !realIds.has(p.id)));
  }, [conversation]);

  const events = useMemo(() => {
    if (!conversation) return [];
    return [...conversation.events, ...pending].sort((a, b) => new Date(a.occurred_at) - new Date(b.occurred_at));
  }, [conversation, pending]);

  const handleSent = (optimisticEvent) => {
    setPending((prev) => [...prev, optimisticEvent]);
    if (leadId != null) markConversationSeen(leadId);
  };

  if (!conversation) {
    return (
      <section className="flex min-w-0 flex-1 items-center justify-center" data-testid="conversation-thread">
        <EmptyState icon={MessagesSquare} title="Select a conversation" description="Choose a lead from the list to view its full communication history." />
      </section>
    );
  }

  const displayName = leadSummary?.name || `Lead #${leadId}`;
  const initials = leadSummary?.name
    ? leadSummary.name.split(" ").map((w) => w[0]).slice(0, 2).join("").toUpperCase()
    : String(leadId).slice(0, 2);

  return (
    <section className="flex min-w-0 flex-1 flex-col" data-testid="conversation-thread">
      <div className="flex items-center justify-between gap-3 border-b border-border p-4">
        <div className="flex min-w-0 items-center gap-3">
          <Avatar className="h-10 w-10 shrink-0">
            <AvatarFallback className="bg-primary/10 text-xs font-semibold text-primary">{initials}</AvatarFallback>
          </Avatar>
          <div className="min-w-0">
            <h3 className="truncate text-sm font-bold">{displayName}</h3>
            <div className="mt-0.5 flex flex-wrap items-center gap-x-3 gap-y-0.5 text-xs text-muted-foreground">
              {leadSummary?.phone && <span className="flex items-center gap-1"><Phone className="h-3 w-3" /> {leadSummary.phone}</span>}
              {leadSummary?.email && <span className="flex items-center gap-1"><Mail className="h-3 w-3" /> {leadSummary.email}</span>}
              {leadSummaryError && <span title="JAWIS unreachable">Identity unavailable</span>}
              <span>Last seen: {formatDateTimeWithRelative(conversation.lastActivityAt)}</span>
            </div>
            <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
              {conversation.channels.length === 0 ? (
                <ChannelBadge channel="system" />
              ) : (
                conversation.channels.map((ch) => <ChannelBadge key={ch} channel={ch} />)
              )}
              {currentInstance && (
                <span className="inline-flex items-center gap-1 rounded-md bg-secondary px-1.5 py-0.5 text-[10px] font-medium">
                  <span className={`h-1.5 w-1.5 rounded-full ${currentInstance.status === "running" ? "bg-emerald-500" : "bg-amber-500"}`} />
                  {journeyName || "Journey"} · {currentInstance.status}
                </span>
              )}
            </div>
          </div>
        </div>
        <Button variant="outline" size="sm" className="h-8 shrink-0 text-xs" asChild>
          <Link to={`/leads/${leadId}`}>
            <ExternalLink className="mr-1.5 h-3.5 w-3.5" /> Full Lead Activity
          </Link>
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-thin bg-secondary/10 p-6">
        <ChatThread events={events} />
      </div>

      <MessageComposer leadId={leadId} leadStage={leadSummary?.stage} onSent={handleSent} />
    </section>
  );
}

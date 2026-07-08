import { useEffect } from "react";
import { Link } from "react-router-dom";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import EmptyState from "@/components/EmptyState";
import { CommunicationTimeline } from "@/modules/journeys";
import ChannelBadge from "./ChannelBadge";
import { markConversationSeen } from "./unreadTracker";
import { MessagesSquare, ExternalLink } from "lucide-react";

/**
 * "Selecting a conversation opens the full history" — this is the detail
 * pane. It renders CommunicationTimeline directly (the exact same shared
 * component ExecutionDrawer and the Lead Activity page use) rather than a
 * second, competing history view.
 */
export default function ConversationThread({ conversation }) {
  const leadId = conversation?.leadId;

  useEffect(() => {
    if (leadId != null) markConversationSeen(leadId);
  }, [leadId]);

  if (!conversation) {
    return (
      <section className="flex min-w-0 flex-1 items-center justify-center" data-testid="conversation-thread">
        <EmptyState icon={MessagesSquare} title="Select a conversation" description="Choose a lead from the list to view its full communication history." />
      </section>
    );
  }

  return (
    <section className="flex min-w-0 flex-1 flex-col" data-testid="conversation-thread">
      <div className="flex items-center justify-between border-b border-border p-4">
        <div className="flex items-center gap-3">
          <Avatar className="h-10 w-10">
            <AvatarFallback className="bg-primary/10 text-xs font-semibold text-primary">
              {String(leadId).slice(0, 2)}
            </AvatarFallback>
          </Avatar>
          <div>
            <h3 className="text-sm font-bold">Lead #{leadId}</h3>
            <div className="mt-0.5 flex flex-wrap items-center gap-1.5">
              {conversation.channels.length === 0 ? (
                <ChannelBadge channel="system" />
              ) : (
                conversation.channels.map((ch) => <ChannelBadge key={ch} channel={ch} />)
              )}
              <span className="text-[11px] text-muted-foreground">
                Last activity: {conversation.lastActivityAt ? new Date(conversation.lastActivityAt).toLocaleString() : "—"}
              </span>
            </div>
          </div>
        </div>
        <Button variant="outline" size="sm" className="h-8 text-xs" asChild>
          <Link to={`/leads/${leadId}`}>
            <ExternalLink className="mr-1.5 h-3.5 w-3.5" /> Full Lead Activity
          </Link>
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-thin bg-secondary/10 p-6">
        <CommunicationTimeline events={conversation.events} />
      </div>
    </section>
  );
}

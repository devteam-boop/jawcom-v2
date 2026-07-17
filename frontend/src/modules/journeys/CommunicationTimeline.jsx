import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import StatusBadge from "@/components/StatusBadge";
import { formatDateTimeWithRelative } from "@/lib/dateFormat";
import {
  Rocket,
  Zap,
  GitBranch,
  Clock,
  MessageCircle,
  Mail,
  StickyNote,
  ClipboardList,
  CheckCircle2,
  ChevronRight,
  ChevronDown,
  Activity,
} from "lucide-react";

const EVENT_META = {
  journey_started: { icon: Rocket, label: "Journey Started", status: "Started", tone: "info" },
  trigger_executed: { icon: Zap, label: "Trigger Executed", status: "Completed", tone: "success" },
  condition_evaluated: { icon: GitBranch, label: "Condition Evaluated", status: "Completed", tone: "success" },
  wait_started: { icon: Clock, label: "Wait Started", status: "Waiting", tone: "warning" },
  wait_completed: { icon: Clock, label: "Wait Completed", status: "Completed", tone: "success" },
  whatsapp_sent: { icon: MessageCircle, label: "WhatsApp Sent", status: "Sent", tone: "success" },
  email_sent: { icon: Mail, label: "Email Sent", status: "Sent", tone: "success" },
  note_added: { icon: StickyNote, label: "Note Added", status: "Completed", tone: "success" },
  task_created: { icon: ClipboardList, label: "Task Created", status: "Created", tone: "warning" },
  task_completed: { icon: CheckCircle2, label: "Task Completed", status: "Completed", tone: "success" },
};

function metaFor(eventType) {
  return (
    EVENT_META[eventType] || {
      icon: Activity,
      label: eventType
        ? eventType.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
        : "Event",
      status: "Recorded",
      tone: "neutral",
    }
  );
}

/**
 * Chronological Communication Timeline for a single running instance.
 * Read-only view over GET /api/communication-events — reuses the dot-list
 * pattern from ExecutionDrawer's execution "Timeline" tab. Each row shows
 * icon/title/timestamp/status/channel/provider; clicking a row expands the
 * raw event payload as JSON.
 */
export default function CommunicationTimeline({ events = [] }) {
  const [expanded, setExpanded] = useState(() => new Set());

  const toggle = (key) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  if (events.length === 0) {
    return <div className="text-sm text-muted-foreground">No communication events yet.</div>;
  }

  return (
    <ol className="relative space-y-4 border-l border-border pl-5">
      {events.map((event, i) => {
        const meta = metaFor(event.event_type);
        const Icon = meta.icon;
        const key = event.id || i;
        const isOpen = expanded.has(key);

        return (
          <li key={key} className="relative">
            <span className="absolute -left-[27px] top-0.5 flex h-5 w-5 items-center justify-center rounded-full border-2 border-background bg-primary/10">
              <Icon className="h-3 w-3 text-primary" />
            </span>

            <button
              type="button"
              onClick={() => toggle(key)}
              className="flex w-full flex-col items-start gap-1 text-left"
              aria-expanded={isOpen}
            >
              <div className="text-xs text-muted-foreground">
                {formatDateTimeWithRelative(event.occurred_at)}
              </div>
              <div className="flex flex-wrap items-center gap-1.5">
                <span className="text-sm font-medium">{meta.label}</span>
                <StatusBadge status={meta.status} tone={meta.tone} />
                {event.channel && (
                  <Badge variant="outline" className="text-[10px] capitalize">{event.channel}</Badge>
                )}
                {event.provider && (
                  <Badge variant="outline" className="text-[10px] capitalize">{event.provider}</Badge>
                )}
                {isOpen ? (
                  <ChevronDown className="h-3 w-3 text-muted-foreground" />
                ) : (
                  <ChevronRight className="h-3 w-3 text-muted-foreground" />
                )}
              </div>
              {event.node_id && (
                <span className="text-[10px] text-muted-foreground">{event.node_id}</span>
              )}
            </button>

            {isOpen && (
              <pre className="mt-2 max-h-[300px] overflow-auto rounded-lg border border-border bg-card p-3 text-xs">
                {JSON.stringify(event.payload || {}, null, 2)}
              </pre>
            )}
          </li>
        );
      })}
    </ol>
  );
}

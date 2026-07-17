import { useMemo, useState } from "react";
import { cn } from "@/lib/utils";
import { formatDateTimeWithRelative, formatTime } from "@/lib/dateFormat";
import { groupIntoChatItems } from "./chatGrouping";
import { Check, CheckCheck, AlertTriangle, Zap, MessageCircle, Mail, ChevronDown, ChevronRight } from "lucide-react";

const CHANNEL_ICON = { whatsapp: MessageCircle, email: Mail };

function StatusIndicator({ item }) {
  if (item.direction !== "out" || !item.status) return null;
  if (item.status === "failed" || item.status === "bounced" || item.status === "complained") {
    return (
      <span className="inline-flex items-center gap-1 text-rose-600 dark:text-rose-400">
        <AlertTriangle className="h-3 w-3" /> {item.status === "failed" ? "Failed" : item.status === "bounced" ? "Bounced" : "Complained"}
      </span>
    );
  }
  if (item.status === "read") {
    return (
      <span className="inline-flex items-center gap-1 text-primary">
        <CheckCheck className="h-3 w-3" /> Read {item.readAt ? formatTime(item.readAt) : ""}
      </span>
    );
  }
  if (item.status === "delivered" || item.status === "clicked") {
    return (
      <span className="inline-flex items-center gap-1 text-muted-foreground">
        <CheckCheck className="h-3 w-3" /> Delivered
      </span>
    );
  }
  // sent/whatsapp_sent/email_sent — accepted but not yet delivered
  return (
    <span className="inline-flex items-center gap-1 text-muted-foreground">
      <Check className="h-3 w-3" /> Sent
    </span>
  );
}

function Bubble({ item }) {
  const [open, setOpen] = useState(false);
  const isOut = item.direction === "out";
  const Icon = CHANNEL_ICON[item.channel] || MessageCircle;

  return (
    <div className={cn("flex", isOut ? "justify-end" : "justify-start")} data-testid={`chat-bubble-${item.key}`}>
      <div className={cn("max-w-[75%]", isOut && "text-right")}>
        <div
          className={cn(
            "rounded-2xl px-4 py-2.5 text-sm shadow-sm",
            isOut ? "rounded-br-md bg-primary text-primary-foreground" : "rounded-bl-md border border-border bg-card"
          )}
        >
          {item.subject && <div className="mb-1 font-semibold">{item.subject}</div>}
          <div className="whitespace-pre-wrap text-left">{item.text}</div>
        </div>

        <div className={cn("mt-1 flex flex-wrap items-center gap-2 text-[11px] text-muted-foreground", isOut ? "justify-end" : "justify-start")}>
          <span className="inline-flex items-center gap-1"><Icon className="h-3 w-3" /> {item.channel || "—"}</span>
          {item.source === "automation" && (
            <span className="inline-flex items-center gap-0.5 rounded bg-secondary px-1 py-0.5"><Zap className="h-2.5 w-2.5" /> Automated</span>
          )}
          <span>{formatTime(item.anchorTime)}</span>
          <StatusIndicator item={item} />
          <button type="button" onClick={() => setOpen((o) => !o)} className="inline-flex items-center hover:text-foreground" data-testid={`chat-bubble-details-${item.key}`}>
            {open ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />} Details
          </button>
        </div>

        {item.errorReason && (
          <p className={cn("mt-1 text-[11px] text-rose-600 dark:text-rose-400", isOut && "text-right")}>{item.errorReason}</p>
        )}

        {open && (
          <pre className="mt-1.5 max-h-64 overflow-auto rounded-lg border border-border bg-secondary/30 p-2 text-left text-[10px]">
            {JSON.stringify(item.raw, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
}

function SystemSeparator({ item }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="flex flex-col items-center gap-1" data-testid={`chat-system-${item.key}`}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="rounded-full bg-secondary px-3 py-1 text-[11px] text-muted-foreground hover:bg-secondary/80"
      >
        {item.label}
        {item.detail ? `: ${item.detail}` : ""} · {formatTime(item.anchorTime)}
      </button>
      {open && (
        <pre className="max-h-48 w-full max-w-md overflow-auto rounded-lg border border-border bg-secondary/30 p-2 text-[10px]">
          {JSON.stringify(item.raw, null, 2)}
        </pre>
      )}
    </div>
  );
}

/**
 * WhatsApp-Business-style rendering of a conversation's communication_events
 * — display only, reuses the exact same events CommunicationTimeline reads
 * (no new data, no duplicate records). Delivery/read status is collapsed
 * onto its message bubble instead of rendered as its own card (see
 * chatGrouping.js); journey/system events become small center separators;
 * raw payload JSON is hidden behind a per-item "Details" toggle.
 */
export default function ChatThread({ events = [] }) {
  const items = useMemo(() => groupIntoChatItems(events), [events]);

  if (items.length === 0) {
    return <div className="text-sm text-muted-foreground">No messages yet.</div>;
  }

  let lastDay = null;
  return (
    <div className="space-y-3" data-testid="chat-thread">
      {items.map((item) => {
        const day = item.anchorTime ? new Date(item.anchorTime).toDateString() : null;
        const showDayMarker = day && day !== lastDay;
        lastDay = day;
        return (
          <div key={item.key} className="space-y-3">
            {showDayMarker && (
              <div className="flex justify-center">
                <span className="rounded-full bg-secondary px-3 py-1 text-[11px] text-muted-foreground">
                  {formatDateTimeWithRelative(item.anchorTime).split(",")[0]}
                </span>
              </div>
            )}
            {item.type === "bubble" ? <Bubble item={item} /> : <SystemSeparator item={item} />}
          </div>
        );
      })}
    </div>
  );
}

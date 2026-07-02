import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const TONE = {
  success: "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-500/20",
  warning: "bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-500/20",
  danger: "bg-rose-500/10 text-rose-700 dark:text-rose-400 border-rose-500/20",
  info: "bg-primary/10 text-primary border-primary/20",
  neutral: "bg-secondary text-secondary-foreground border-border",
};

const STATUS_TONE = {
  Active: "success",
  Running: "success",
  Connected: "success",
  Won: "success",
  Open: "info",
  Scheduled: "info",
  Qualified: "info",
  Proposal: "info",
  Negotiation: "warning",
  Draft: "neutral",
  Paused: "warning",
  Lead: "warning",
  New: "warning",
  Inactive: "neutral",
  Closed: "neutral",
  Completed: "neutral",
  Assigned: "neutral",
  Unread: "danger",
  Lost: "danger",
  Overdue: "danger",
};

export default function StatusBadge({ status, tone, className }) {
  const t = tone || STATUS_TONE[status] || "neutral";
  return (
    <Badge
      variant="outline"
      className={cn("font-medium", TONE[t], className)}
      data-testid={`status-${status}`}
    >
      {status}
    </Badge>
  );
}

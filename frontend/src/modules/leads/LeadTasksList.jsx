import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import StatusBadge from "@/components/StatusBadge";
import EmptyState from "@/components/EmptyState";
import { formatDateTimeWithRelative, formatDate } from "@/lib/dateFormat";
import { ClipboardList, ExternalLink } from "lucide-react";

const STATUS_TONE = { completed: "success", rejected: "danger", pending: "warning" };
const PRIORITY_TONE = { urgent: "danger", high: "danger", medium: "warning", low: "neutral" };

/**
 * Tasks aggregated across every running instance for this lead. Fetched via
 * the existing per-instance GET /api/tasks/{instance_id} (fanned out in
 * useLeadActivity) — there is no lead-scoped tasks endpoint, and adding one
 * is out of scope (no backend redesign). Read-only here: task
 * resolution (Complete/Reject) already exists in ExecutionDrawer's Tasks
 * tab, reached via the "View" action instead of being re-implemented here.
 */
export default function LeadTasksList({ tasks = [], onOpenInstance }) {
  if (tasks.length === 0) {
    return (
      <EmptyState
        icon={ClipboardList}
        title="No tasks yet"
        description="Manual tasks created by a journey's Task node will appear here."
      />
    );
  }

  return (
    <div className="space-y-2">
      {tasks.map((t) => (
        <Card key={t.id} className="rounded-lg border-border p-3">
          <div className="flex items-center justify-between gap-2">
            <span className="flex items-center gap-2 text-sm font-medium">
              <ClipboardList className="h-4 w-4 text-orange-500" />
              {t.title}
            </span>
            <div className="flex items-center gap-1.5">
              {t.priority && <StatusBadge status={t.priority} tone={PRIORITY_TONE[t.priority] || "neutral"} />}
              <StatusBadge status={t.status} tone={STATUS_TONE[t.status] || "warning"} />
              {onOpenInstance && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6"
                  onClick={() => onOpenInstance(t.instance_id)}
                  title="View journey instance"
                >
                  <ExternalLink className="h-3.5 w-3.5" />
                </Button>
              )}
            </div>
          </div>
          {t.description && <p className="mt-1.5 text-xs text-muted-foreground">{t.description}</p>}
          <div className="mt-2 flex flex-wrap gap-2 text-xs text-muted-foreground">
            <span>Assignee: {t.assignee || "—"}</span>
            {t.due_date && <span>Due: {formatDate(t.due_date)}</span>}
            <span>Created: {formatDateTimeWithRelative(t.created_at)}</span>
          </div>
        </Card>
      ))}
    </div>
  );
}

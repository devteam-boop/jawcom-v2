import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import StatusBadge from "@/components/StatusBadge";
import { aiAssistantService } from "@/services/aiAssistant";
import {
  Sparkles,
  Phone,
  MessageCircle,
  Mail,
  CalendarClock,
  FileText,
  RotateCcw,
  XCircle,
  CheckCircle2,
  Flame,
  Sun,
  Snowflake,
  Loader2,
  RefreshCw,
} from "lucide-react";

const ACTION_META = {
  call: { icon: Phone, label: "Call" },
  whatsapp: { icon: MessageCircle, label: "WhatsApp" },
  email: { icon: Mail, label: "Email" },
  schedule_visit: { icon: CalendarClock, label: "Schedule Visit" },
  send_proposal: { icon: FileText, label: "Send Proposal" },
  follow_up: { icon: RotateCcw, label: "Follow Up" },
  close_lost: { icon: XCircle, label: "Close Lost" },
  mark_qualified: { icon: CheckCircle2, label: "Mark Qualified" },
};

const HEALTH_META = {
  hot: { icon: Flame, tone: "danger", label: "Hot" },
  warm: { icon: Sun, tone: "warning", label: "Warm" },
  cold: { icon: Snowflake, tone: "info", label: "Cold" },
};

/**
 * AI Lead Assistant — summary, next-best-action, reply suggestion, and lead
 * health, generated on demand via GET /api/leads/{id}/ai-assistant.
 *
 * Deliberately manual (button-triggered), not auto-fetched on mount: each
 * generation is a real Claude API call with no caching or persistence (no
 * database changes per scope), so auto-firing on every page view would mean
 * an LLM call every time this page loads.
 */
export default function AIAssistantPanel({ leadId }) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const generate = () => {
    if (!leadId) return;
    setLoading(true);
    setError(null);
    aiAssistantService
      .get(leadId)
      .then((data) => setResult(data))
      .catch((err) => setError(err))
      .finally(() => setLoading(false));
  };

  const health = result ? HEALTH_META[result.lead_health] : null;
  const HealthIcon = health?.icon;
  const action = result ? ACTION_META[result.next_best_action] : null;
  const ActionIcon = action?.icon;

  return (
    <Card className="rounded-xl border-border bg-card p-5" data-testid="ai-assistant-panel">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-primary" />
          <h3 className="text-sm font-semibold">AI Lead Assistant</h3>
        </div>
        <Button size="sm" variant="outline" className="h-7 text-xs" onClick={generate} disabled={loading}>
          {loading ? (
            <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
          ) : (
            <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
          )}
          {result ? "Regenerate" : "Generate Insights"}
        </Button>
      </div>

      {error && (
        <div className="mt-3 rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
          {error?.message || "AI Assistant unavailable."}
        </div>
      )}

      {!result && !error && !loading && (
        <p className="mt-3 text-xs text-muted-foreground">
          Generate a summary, next-best-action recommendation, reply suggestion, and health score for this lead.
        </p>
      )}

      {result && (
        <div className="mt-4 space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            {health && (
              <span className="inline-flex items-center gap-1.5">
                <HealthIcon className="h-4 w-4 text-muted-foreground" />
                <StatusBadge status={health.label} tone={health.tone} />
              </span>
            )}
          </div>

          <div>
            <div className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Summary</div>
            <ul className="space-y-1 text-sm">
              {result.summary.map((bullet, i) => (
                <li key={i} className="flex gap-2">
                  <span className="text-muted-foreground">•</span>
                  <span>{bullet}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="rounded-lg border border-border bg-secondary/30 p-3">
            <div className="flex items-center gap-2 text-sm font-semibold">
              {ActionIcon && <ActionIcon className="h-3.5 w-3.5 text-primary" />}
              Next Best Action: {action?.label || result.next_best_action}
            </div>
            <p className="mt-1 text-xs text-muted-foreground">{result.next_best_action_reason}</p>
          </div>

          {result.reply_suggestion && (
            <div>
              <div className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Suggested Reply
              </div>
              <p className="rounded-lg border border-border bg-card p-3 text-sm">{result.reply_suggestion}</p>
            </div>
          )}
        </div>
      )}
    </Card>
  );
}

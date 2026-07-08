import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import StatusBadge from "@/components/StatusBadge";
import { aiSummaryService } from "@/services/aiSummary";
import { Sparkles, Loader2, RefreshCw } from "lucide-react";

const HEALTH_TONE = { Hot: "danger", Warm: "warning", Cold: "info" };

/**
 * Lightweight AI Summary card — GET /api/leads/{id}/ai-summary.
 * Separate, smaller sibling of AIAssistantPanel; not auto-fetched — only
 * loads when "Generate Summary" is clicked (no caching/persistence backing
 * it, so an auto-fetch would mean an LLM call on every page view).
 */
export default function AISummaryCard({ leadId }) {
  const [result, setResult] = useState(null);
  const [unavailable, setUnavailable] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const generate = () => {
    if (!leadId) return;
    setLoading(true);
    setError(null);
    setUnavailable(false);
    aiSummaryService
      .get(leadId)
      .then((data) => {
        if (data?.status === "ai_unavailable") {
          setUnavailable(true);
          setResult(null);
        } else {
          setResult(data);
        }
      })
      .catch((err) => setError(err))
      .finally(() => setLoading(false));
  };

  return (
    <Card className="rounded-xl border-border bg-card p-5" data-testid="ai-summary-card">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-primary" />
          <h3 className="text-sm font-semibold">AI Summary</h3>
        </div>
        <Button size="sm" variant="outline" className="h-7 text-xs" onClick={generate} disabled={loading}>
          {loading ? (
            <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
          ) : (
            <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
          )}
          {result ? "Regenerate" : "Generate Summary"}
        </Button>
      </div>

      {error && (
        <p className="mt-3 text-xs text-red-600 dark:text-red-400">
          {error?.message || "Failed to generate summary."}
        </p>
      )}

      {unavailable && !error && (
        <p className="mt-3 text-xs text-muted-foreground">AI summary is currently unavailable.</p>
      )}

      {!result && !unavailable && !error && !loading && (
        <p className="mt-3 text-xs text-muted-foreground">Click "Generate Summary" for a quick AI overview of this lead.</p>
      )}

      {result && (
        <div className="mt-3 space-y-3">
          <StatusBadge status={result.lead_health} tone={HEALTH_TONE[result.lead_health] || "neutral"} />

          <ul className="space-y-1 text-sm">
            {result.summary.map((bullet, i) => (
              <li key={i} className="flex gap-2">
                <span className="text-muted-foreground">•</span>
                <span>{bullet}</span>
              </li>
            ))}
          </ul>

          <div>
            <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Journey Summary</div>
            <p className="mt-1 text-sm">{result.journey_summary}</p>
          </div>

          <div className="rounded-lg border border-border bg-secondary/30 p-3">
            <div className="text-sm font-semibold">Next Best Action: {result.next_best_action}</div>
            <p className="mt-1 text-xs text-muted-foreground">{result.reason}</p>
          </div>
        </div>
      )}
    </Card>
  );
}

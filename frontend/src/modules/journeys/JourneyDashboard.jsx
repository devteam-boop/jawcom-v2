import { useState, useEffect, useMemo } from "react";
import StatCard from "@/components/StatCard";
import ChartCard from "@/components/ChartCard";
import EmptyState from "@/components/EmptyState";
import StatusBadge from "@/components/StatusBadge";
import { Button } from "@/components/ui/button";
import { flowDefinitionService } from "@/services/flowDefinitions";
import { integrationService } from "@/services/integrations";
import {
  Activity,
  CheckCircle2,
  XCircle,
  Clock,
  TrendingUp,
  Timer,
  Workflow,
  GitBranch,
  Play,
  Pause,
  Archive,
  MessageCircle,
  Mail,
  Users,
  Zap,
} from "lucide-react";

const JOURNEY_STATUS_TONE = {
  draft: "neutral",
  active: "success",
  paused: "warning",
  archived: "neutral",
};

const INTEGRATION_META = {
  whatsapp: { label: "WhatsApp", icon: MessageCircle },
  email: { label: "Email", icon: Mail },
  crm: { label: "CRM", icon: Users },
  jawis: { label: "JAWIS", icon: Zap },
};

function formatAverageDuration(ms) {
  if (ms == null) return "—";
  const seconds = Math.round(ms / 1000);
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ${seconds % 60}s`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h ${minutes % 60}m`;
}

export default function JourneyDashboard({
  journey,
  instances = [],
  mappings = [],
  actionLoading = false,
  onAction,
  onTestJourney,
  onOpenFlow,
}) {
  const [flowDef, setFlowDef] = useState(null);
  const [flowLoading, setFlowLoading] = useState(true);
  const [validation, setValidation] = useState(null);
  const [health, setHealth] = useState(null);

  useEffect(() => {
    let active = true;
    if (!journey?.flow_definition_id) {
      setFlowDef(null);
      setValidation(null);
      setFlowLoading(false);
      return undefined;
    }
    setFlowLoading(true);
    flowDefinitionService
      .get(journey.flow_definition_id)
      .then((def) => {
        if (!active) return null;
        setFlowDef(def);
        return flowDefinitionService.validate(def.id);
      })
      .then((result) => {
        if (active && result) setValidation(result);
      })
      .catch(() => {
        if (active) {
          setFlowDef(null);
          setValidation(null);
        }
      })
      .finally(() => {
        if (active) setFlowLoading(false);
      });
    return () => {
      active = false;
    };
  }, [journey?.flow_definition_id]);

  useEffect(() => {
    let active = true;
    integrationService
      .getHealth()
      .then((data) => {
        if (active) setHealth(data);
      })
      .catch(() => {
        if (active) setHealth(null);
      });
    return () => {
      active = false;
    };
  }, []);

  const metrics = useMemo(() => {
    const total = instances.length;
    const running = instances.filter((i) => i.status === "running").length;
    const waiting = instances.filter((i) =>
      ["waiting", "waiting_approval", "waiting_task"].includes(i.status)
    ).length;
    const completed = instances.filter((i) => i.status === "completed").length;
    const failed = instances.filter((i) => i.status === "failed").length;
    const successRate = total > 0 ? Math.round((completed / total) * 100) : 0;

    const durations = instances
      .map((i) =>
        i.started_at && i.completed_at
          ? new Date(i.completed_at) - new Date(i.started_at)
          : null
      )
      .filter((d) => d != null && d >= 0);
    const avgMs =
      durations.length > 0
        ? durations.reduce((a, b) => a + b, 0) / durations.length
        : null;

    return { total, running, waiting, completed, failed, successRate, avgMs };
  }, [instances]);

  const isActive = journey?.status === "active";
  const isPaused = journey?.status === "paused";
  const nodeCount = flowDef?.definition?.nodes?.length ?? 0;
  const edgeCount = flowDef?.definition?.edges?.length ?? 0;
  const hasErrors = validation && !validation.valid;

  return (
    <div className="space-y-6" data-testid="journey-dashboard">
      {/* Journey Summary */}
      <ChartCard title="Journey Summary" description="Overview of this journey's configuration.">
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
          <SummaryField label="Name" value={journey?.name || "—"} />
          <SummaryField
            label="Status"
            value={<StatusBadge status={journey?.status || "—"} tone={JOURNEY_STATUS_TONE[journey?.status]} />}
          />
          <SummaryField label="Trigger Stage" value={mappings[0]?.stage_key || "Not configured"} />
          <SummaryField label="Current Version" value={flowDef ? `v${flowDef.version}` : "—"} />
          <SummaryField
            label="Created At"
            value={journey?.created_at ? new Date(journey.created_at).toLocaleString() : "—"}
          />
          <SummaryField
            label="Last Published"
            value={
              flowDef?.status === "published"
                ? new Date(flowDef.updated_at).toLocaleString()
                : "Not yet published"
            }
          />
        </div>
      </ChartCard>

      {/* Execution Metrics */}
      <div>
        <h3 className="mb-3 text-sm font-bold">Execution Metrics</h3>
        {metrics.total === 0 ? (
          <EmptyState
            icon={Activity}
            title="No executions yet"
            description="Once leads enter this journey, execution metrics will appear here."
          />
        ) : (
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4 lg:grid-cols-7">
            <StatCard label="Total" value={metrics.total} icon={Workflow} />
            <StatCard label="Running" value={metrics.running} icon={Activity} />
            <StatCard label="Waiting" value={metrics.waiting} icon={Clock} />
            <StatCard label="Completed" value={metrics.completed} icon={CheckCircle2} />
            <StatCard label="Failed" value={metrics.failed} icon={XCircle} />
            <StatCard label="Success Rate" value={`${metrics.successRate}%`} icon={TrendingUp} />
            <StatCard label="Avg Duration" value={formatAverageDuration(metrics.avgMs)} icon={Timer} />
          </div>
        )}
      </div>

      {/* Flow Summary */}
      <ChartCard title="Flow Summary" description="Structure and validation status of the flow.">
        {flowLoading ? (
          <div className="text-sm text-muted-foreground">Loading…</div>
        ) : !journey?.flow_definition_id ? (
          <EmptyState
            icon={GitBranch}
            title="No flow created yet"
            description="Build a flow for this journey to see its summary here."
          />
        ) : (
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
            <MetaRow label="Total Nodes" value={nodeCount} />
            <MetaRow label="Total Connections" value={edgeCount} />
            <MetaRow
              label="Validation Status"
              value={
                validation ? (
                  <StatusBadge
                    status={hasErrors ? `${validation.errors.length} error(s)` : "Valid"}
                    tone={hasErrors ? "danger" : "success"}
                  />
                ) : (
                  "—"
                )
              }
            />
            <MetaRow
              label="Published Version"
              value={flowDef?.status === "published" ? `v${flowDef.version}` : "Not published"}
            />
          </div>
        )}
      </ChartCard>

      {/* Integration Status */}
      <ChartCard title="Integration Status" description="Live health of external services used by this journey.">
        {!health ? (
          <div className="text-sm text-muted-foreground">Loading…</div>
        ) : (
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            {Object.entries(INTEGRATION_META).map(([key, meta]) => {
              const Icon = meta.icon;
              const isHealthy = health[key]?.status === "healthy";
              return (
                <div key={key} className="flex items-center gap-2.5 rounded-lg border border-border p-3">
                  <Icon className="h-4 w-4 shrink-0 text-muted-foreground" />
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-xs font-semibold">{meta.label}</div>
                    <StatusBadge status={isHealthy ? "Active" : "Inactive"} tone={isHealthy ? "success" : "neutral"} />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </ChartCard>

      {/* Quick Actions */}
      <ChartCard title="Quick Actions">
        <div className="flex flex-wrap gap-2">
          <Button size="sm" variant="outline" onClick={onTestJourney} data-testid="quick-action-test">
            <Play className="mr-2 h-3.5 w-3.5" /> Test Journey
          </Button>
          <Button size="sm" variant="outline" onClick={onOpenFlow} data-testid="quick-action-open-flow">
            <Workflow className="mr-2 h-3.5 w-3.5" /> Open Flow
          </Button>
          {isActive && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => onAction?.("pause")}
              disabled={actionLoading}
              data-testid="quick-action-pause"
            >
              <Pause className="mr-2 h-3.5 w-3.5" /> Pause
            </Button>
          )}
          {isPaused && (
            <Button
              size="sm"
              onClick={() => onAction?.("activate")}
              disabled={actionLoading}
              data-testid="quick-action-resume"
            >
              <Play className="mr-2 h-3.5 w-3.5" /> Resume
            </Button>
          )}
          {(isActive || isPaused) && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => onAction?.("archive")}
              disabled={actionLoading}
              data-testid="quick-action-archive"
            >
              <Archive className="mr-2 h-3.5 w-3.5" /> Archive
            </Button>
          )}
        </div>
      </ChartCard>
    </div>
  );
}

function SummaryField({ label, value }) {
  return (
    <div>
      <div className="text-[11px] uppercase tracking-wider text-muted-foreground">{label}</div>
      <div className="mt-0.5 text-sm font-medium">{value}</div>
    </div>
  );
}

function MetaRow({ label, value }) {
  return (
    <div className="flex items-center justify-between border-b border-border/60 pb-2 text-sm last:border-b-0 last:pb-0">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}

import { useState, useEffect, useMemo, useCallback } from "react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import {
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";
import StatusBadge from "@/components/StatusBadge";
import { runningInstanceService } from "@/services/runningInstances";
import { journeyService } from "@/services/journeys";
import { flowExecutionLogService } from "@/services/flowExecutionLogs";
import { approvalService } from "@/services/approvals";
import { taskService } from "@/services/tasks";
import { communicationEventService } from "@/services/communicationEvents";
import { formatDateTimeWithRelative, formatDate, formatDateTimeSeconds } from "@/lib/dateFormat";
import CommunicationTimeline from "./CommunicationTimeline";
import { toast } from "sonner";
import {
  Workflow,
  Play,
  RotateCcw,
  AlertCircle,
  ThumbsUp,
  ClipboardList,
  CheckCircle2,
  XCircle,
  ChevronDown,
  ChevronRight,
} from "lucide-react";

export const INSTANCE_STATUS_TONE = {
  pending: "neutral",
  running: "info",
  waiting: "warning",
  waiting_approval: "warning",
  waiting_task: "warning",
  paused: "warning",
  failed: "danger",
  completed: "success",
  cancelled: "neutral",
};

const NODE_STATUS_COLORS = {
  success: "bg-emerald-500",
  started: "bg-blue-500",
  waiting: "bg-amber-500",
  failed: "bg-red-500",
  skipped: "bg-gray-400",
  pending: "bg-gray-400",
};

function formatDuration(startedAt, completedAt) {
  if (!startedAt) return "—";
  const start = new Date(startedAt);
  const end = completedAt ? new Date(completedAt) : new Date();
  const diffMs = end - start;
  if (diffMs < 0) return "—";
  const seconds = Math.floor(diffMs / 1000);
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ${seconds % 60}s`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h ${minutes % 60}m`;
}

/**
 * Single reusable running-instance detail drawer, shared by the Running Tab
 * (JourneyDetail) and Journey Monitor. Self-contained: given only an
 * instanceId, it fetches the instance, its journey, execution logs,
 * approvals and tasks itself — callers never fetch or pass this data in.
 */
export default function ExecutionDrawer({ instanceId, onClose, onActionComplete }) {
  const [instance, setInstance] = useState(null);
  const [journeyName, setJourneyName] = useState(null);
  const [logs, setLogs] = useState([]);
  const [approvals, setApprovals] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [communicationEvents, setCommunicationEvents] = useState([]);

  useEffect(() => {
    if (!instanceId) {
      setInstance(null);
      setJourneyName(null);
      setLogs([]);
      setApprovals([]);
      setTasks([]);
      setCommunicationEvents([]);
      return undefined;
    }

    let active = true;

    runningInstanceService
      .get(instanceId)
      .then((fullInstance) => {
        if (!active) return;
        setInstance(fullInstance);
        if (fullInstance.journey_id) {
          journeyService
            .get(fullInstance.journey_id)
            .then((j) => { if (active) setJourneyName(j.name); })
            .catch(() => {});
        }
      })
      .catch(() => { if (active) setInstance(null); });

    flowExecutionLogService
      .list({ runningInstanceId: instanceId })
      .then((data) => { if (active) setLogs(data); })
      .catch(() => { if (active) setLogs([]); });

    communicationEventService
      .list({ runningInstanceId: instanceId })
      .then((data) => { if (active) setCommunicationEvents(data); })
      .catch(() => { if (active) setCommunicationEvents([]); });

    Promise.all([
      approvalService.list(instanceId).catch(() => []),
      taskService.list(instanceId).catch(() => []),
    ]).then(([approvalData, taskData]) => {
      if (!active) return;
      setApprovals(approvalData);
      setTasks(taskData);
    });

    return () => { active = false; };
  }, [instanceId]);

  const row = useMemo(() => {
    if (!instance) return null;
    const leadId = instance.lead_id || "";
    const data = instance.data || {};
    const autoStatus = instance.status || "unknown";
    return {
      id: instance.id,
      lead_id: instance.lead_id,
      name: `Lead #${leadId}`,
      initials: String(leadId).slice(0, 2).toUpperCase() || "??",
      journeyName: journeyName || "—",
      autoStatus,
      current_node_id: data.current_node_id || null,
      resume_at: data.resume_at || null,
      retry_count: data.retry_count || 0,
      started_at: instance.started_at || null,
      completed_at: instance.completed_at || null,
      health: autoStatus === "completed" ? "Healthy" : autoStatus === "failed" ? "Stalled" : "At Risk",
      healthTone: autoStatus === "completed" ? "success" : autoStatus === "failed" ? "danger" : "warning",
    };
  }, [instance, journeyName]);

  const nodeStatuses = useMemo(() => {
    const map = {};
    logs.forEach((log) => {
      map[log.node_id] = {
        node_id: log.node_id,
        status: log.status,
        node_type: log.input?.node_type || "",
        error_message: log.error_message,
        executed_at: log.executed_at || log.created_at,
        raw: log,
      };
    });
    return Object.values(map);
  }, [logs]);

  const [expandedNodeId, setExpandedNodeId] = useState(null);

  const failedLog = useMemo(() => logs.find((log) => log.status === "failed") || null, [logs]);

  const finish = useCallback(() => {
    onActionComplete?.();
    onClose?.();
  }, [onActionComplete, onClose]);

  const handleRetry = useCallback(async (mode = "node") => {
    if (!row) return;
    try {
      const result = await runningInstanceService.retry(row.id, mode);
      if (result.success) {
        toast.success(`Retry ${mode} triggered for ${row.name}`);
        finish();
      } else {
        toast.error("Retry failed — engine returned an error");
      }
    } catch (err) {
      toast.error(err?.response?.data?.detail || err.message || "Retry failed");
    }
  }, [row, finish]);

  const handleResume = useCallback(async () => {
    if (!row) return;
    try {
      const result = await runningInstanceService.resume(row.id);
      if (result.success) {
        toast.success(`Instance ${row.name} resumed`);
        finish();
      } else {
        toast.error("Resume failed — engine returned an error");
      }
    } catch (err) {
      toast.error(err?.response?.data?.detail || err.message || "Resume failed");
    }
  }, [row, finish]);

  const handleApprove = useCallback(async (approvalId) => {
    if (!row) return;
    try {
      const result = await approvalService.approve(row.id, approvalId);
      if (result.resumed) {
        toast.success("Approval resolved — journey resumed");
        finish();
      }
    } catch (err) {
      toast.error(err?.response?.data?.detail || err.message || "Approval failed");
    }
  }, [row, finish]);

  const handleReject = useCallback(async (approvalId) => {
    if (!row) return;
    try {
      const result = await approvalService.reject(row.id, approvalId);
      if (result.resumed) {
        toast.success("Approval rejected — journey resumed");
        finish();
      }
    } catch (err) {
      toast.error(err?.response?.data?.detail || err.message || "Rejection failed");
    }
  }, [row, finish]);

  const handleCompleteTask = useCallback(async (taskId) => {
    if (!row) return;
    try {
      const result = await taskService.complete(row.id, taskId);
      if (result.resumed) {
        toast.success("Task completed — journey resumed");
        finish();
      }
    } catch (err) {
      toast.error(err?.response?.data?.detail || err.message || "Task completion failed");
    }
  }, [row, finish]);

  const handleRejectTask = useCallback(async (taskId) => {
    if (!row) return;
    try {
      const result = await taskService.reject(row.id, taskId);
      if (result.resumed) {
        toast.success("Task rejected — journey resumed");
        finish();
      }
    } catch (err) {
      toast.error(err?.response?.data?.detail || err.message || "Task rejection failed");
    }
  }, [row, finish]);

  return (
    <Sheet open={!!instanceId} onOpenChange={(open) => !open && onClose?.()}>
      <SheetContent side="right" className="w-full overflow-y-auto p-0 sm:max-w-md">
        {row && (
          <>
            <SheetHeader className="border-b border-border p-6">
              <div className="flex items-start gap-4">
                <Avatar className="h-14 w-14">
                  <AvatarFallback className="bg-primary/10 text-base font-semibold text-primary">{row.initials}</AvatarFallback>
                </Avatar>
                <div className="min-w-0 flex-1 text-left">
                  <SheetTitle className="truncate text-lg">{row.name}</SheetTitle>
                  <p className="mt-1 truncate text-xs text-muted-foreground">{row.journeyName}</p>
                  <p className="mt-2 flex flex-wrap gap-1.5">
                    <StatusBadge status={row.autoStatus} tone={INSTANCE_STATUS_TONE[row.autoStatus]} />
                    <StatusBadge status={row.health === "Healthy" ? "Active" : row.health === "At Risk" ? "Open" : "Lost"} tone={row.healthTone} />
                  </p>
                </div>
              </div>
            </SheetHeader>

            {row.autoStatus === "failed" && failedLog && (
              <div className="mx-6 mt-4 rounded-lg border border-red-200 bg-red-50 p-3 dark:border-red-800 dark:bg-red-950">
                <div className="flex items-start gap-2">
                  <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-600 dark:text-red-400" />
                  <div className="min-w-0 text-xs">
                    <p className="font-semibold text-red-700 dark:text-red-300">Execution Failed</p>
                    <p className="mt-1 text-red-600 dark:text-red-400">
                      <span className="font-medium">Node:</span> {failedLog.node_id}
                    </p>
                    {failedLog.error_message && (
                      <p className="mt-0.5 text-red-600 dark:text-red-400">
                        <span className="font-medium">Reason:</span> {failedLog.error_message}
                      </p>
                    )}
                    <p className="mt-0.5 text-red-600 dark:text-red-400">
                      <span className="font-medium">Time:</span> {formatDateTimeWithRelative(failedLog.executed_at)}
                    </p>
                  </div>
                </div>
              </div>
            )}

            <Tabs defaultValue="overview" className="p-6">
              <TabsList className={`grid w-full grid-cols-${row.autoStatus === 'waiting_approval' || row.autoStatus === 'waiting_task' || approvals.length > 0 || tasks.length > 0 ? '7' : '5'}`}>
                <TabsTrigger value="overview" className="text-xs">Overview</TabsTrigger>
                {(row.autoStatus === 'waiting_approval' || approvals.length > 0) && (
                  <TabsTrigger value="approvals" className="text-xs">Approvals</TabsTrigger>
                )}
                {(row.autoStatus === 'waiting_task' || tasks.length > 0) && (
                  <TabsTrigger value="tasks" className="text-xs">Tasks</TabsTrigger>
                )}
                <TabsTrigger value="steps" className="text-xs">Steps</TabsTrigger>
                <TabsTrigger value="timeline" className="text-xs">Timeline</TabsTrigger>
                <TabsTrigger value="communication" className="text-xs">Communication</TabsTrigger>
                <TabsTrigger value="raw" className="text-xs">Raw</TabsTrigger>
              </TabsList>

              <TabsContent value="overview" className="mt-5 space-y-3 text-sm">
                <div className="rounded-lg border border-border bg-card p-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Workflow className="h-3.5 w-3.5 text-primary" />
                      <span className="text-sm font-semibold">{row.journeyName}</span>
                    </div>
                    <StatusBadge status={row.autoStatus} tone={INSTANCE_STATUS_TONE[row.autoStatus]} />
                  </div>
                </div>
                <MetaRow label="Status" value={row.autoStatus} />
                <MetaRow label="Lead ID" value={String(row.lead_id)} />
                <MetaRow label="Current Node" value={row.current_node_id || "—"} />
                <MetaRow label="Started At" value={formatDateTimeWithRelative(row.started_at)} />
                <MetaRow label="Completed At" value={formatDateTimeWithRelative(row.completed_at)} />
                <MetaRow label="Duration" value={formatDuration(row.started_at, row.completed_at)} />
                <MetaRow label="Health" value={row.health} />
                {row.autoStatus === "waiting" && row.resume_at && (
                  <MetaRow label="Resume At" value={formatDateTimeWithRelative(row.resume_at)} />
                )}
                {row.autoStatus === "waiting_approval" && (
                  <MetaRow label="Paused For" value="Approval" />
                )}
                {row.autoStatus === "waiting_task" && (
                  <MetaRow label="Paused For" value="Manual Task" />
                )}
                {row.retry_count > 0 && (
                  <MetaRow label="Retry Count" value={String(row.retry_count)} />
                )}
                {row.autoStatus === "completed" && (
                  <MetaRow label="Result" value="Completed successfully" />
                )}
                <Separator />
                <div className="grid grid-cols-2 gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-8 text-xs"
                    disabled={row.autoStatus !== "failed"}
                    onClick={() => handleRetry("node")}
                  >
                    <RotateCcw className="mr-2 h-3 w-3" /> Retry
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-8 text-xs"
                    disabled={row.autoStatus !== "waiting" && row.autoStatus !== "waiting_approval" && row.autoStatus !== "waiting_task"}
                    onClick={handleResume}
                  >
                    <Play className="mr-2 h-3 w-3" /> Resume
                  </Button>
                </div>
              </TabsContent>

              {(row.autoStatus === 'waiting_approval' || approvals.length > 0) && (
                <TabsContent value="approvals" className="mt-5 space-y-3">
                  {approvals.length === 0 ? (
                    <div className="text-sm text-muted-foreground">No approvals found.</div>
                  ) : (
                    approvals.map((a) => (
                      <div key={a.id} className="rounded-lg border border-border bg-card p-3">
                        <div className="flex items-center justify-between">
                          <span className="flex items-center gap-2 text-sm font-semibold">
                            <ThumbsUp className="h-4 w-4 text-cyan-500" />
                            {a.title}
                          </span>
                          <StatusBadge status={a.status} tone={a.status === 'approved' ? 'success' : a.status === 'rejected' ? 'danger' : 'warning'} />
                        </div>
                        {a.description && <p className="mt-2 text-xs text-muted-foreground">{a.description}</p>}
                        <div className="mt-2 flex flex-wrap gap-2 text-xs text-muted-foreground">
                          <span>Approver: {a.approver || '—'}</span>
                          <span>Created: {formatDateTimeWithRelative(a.created_at)}</span>
                          {a.resolved_at && <span>Resolved: {formatDateTimeWithRelative(a.resolved_at)}</span>}
                        </div>
                        {a.status === 'pending' && (
                          <div className="mt-3 flex gap-2">
                            <Button size="sm" variant="default" className="h-7 text-xs" onClick={() => handleApprove(a.id)}>
                              <CheckCircle2 className="mr-1 h-3 w-3" /> Approve
                            </Button>
                            <Button size="sm" variant="destructive" className="h-7 text-xs" onClick={() => handleReject(a.id)}>
                              <XCircle className="mr-1 h-3 w-3" /> Reject
                            </Button>
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </TabsContent>
              )}

              {(row.autoStatus === 'waiting_task' || tasks.length > 0) && (
                <TabsContent value="tasks" className="mt-5 space-y-3">
                  {tasks.length === 0 ? (
                    <div className="text-sm text-muted-foreground">No tasks found.</div>
                  ) : (
                    tasks.map((t) => (
                      <div key={t.id} className="rounded-lg border border-border bg-card p-3">
                        <div className="flex items-center justify-between">
                          <span className="flex items-center gap-2 text-sm font-semibold">
                            <ClipboardList className="h-4 w-4 text-orange-500" />
                            {t.title}
                          </span>
                          <div className="flex items-center gap-2">
                            {t.priority && <StatusBadge status={t.priority} tone={t.priority === 'urgent' || t.priority === 'high' ? 'danger' : t.priority === 'medium' ? 'warning' : 'neutral'} />}
                            <StatusBadge status={t.status} tone={t.status === 'completed' ? 'success' : t.status === 'rejected' ? 'danger' : 'warning'} />
                          </div>
                        </div>
                        {t.description && <p className="mt-2 text-xs text-muted-foreground">{t.description}</p>}
                        <div className="mt-2 flex flex-wrap gap-2 text-xs text-muted-foreground">
                          <span>Assignee: {t.assignee || '—'}</span>
                          {t.due_date && <span>Due: {formatDate(t.due_date)}</span>}
                          <span>Created: {formatDateTimeWithRelative(t.created_at)}</span>
                          {t.completed_at && <span>Completed: {formatDateTimeWithRelative(t.completed_at)}</span>}
                        </div>
                        {t.status === 'pending' && (
                          <div className="mt-3 flex gap-2">
                            <Button size="sm" variant="default" className="h-7 text-xs" onClick={() => handleCompleteTask(t.id)}>
                              <CheckCircle2 className="mr-1 h-3 w-3" /> Complete
                            </Button>
                            <Button size="sm" variant="destructive" className="h-7 text-xs" onClick={() => handleRejectTask(t.id)}>
                              <XCircle className="mr-1 h-3 w-3" /> Reject
                            </Button>
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </TabsContent>
              )}

              <TabsContent value="steps" className="mt-5 space-y-2">
                {nodeStatuses.length === 0 ? (
                  <div className="text-sm text-muted-foreground">No execution logs available.</div>
                ) : (
                  nodeStatuses.map((s, i) => {
                    const key = s.node_id || i;
                    const isOpen = expandedNodeId === key;
                    return (
                      <div key={key} className="rounded-lg border border-border">
                        <button
                          type="button"
                          className="flex w-full items-center gap-3 p-2.5 text-left"
                          onClick={() => setExpandedNodeId(isOpen ? null : key)}
                        >
                          <span className={`inline-block h-2.5 w-2.5 shrink-0 rounded-full ${NODE_STATUS_COLORS[s.status] || "bg-gray-400"}`} />
                          <div className="min-w-0 flex-1">
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-medium">{s.node_id}</span>
                              {s.node_type && <Badge variant="outline" className="text-[10px]">{s.node_type}</Badge>}
                            </div>
                            {s.error_message && !isOpen && (
                              <p className="mt-0.5 truncate text-xs text-red-500">{s.error_message}</p>
                            )}
                            <p className="mt-0.5 text-[11px] text-muted-foreground">{formatDateTimeSeconds(s.executed_at)}</p>
                          </div>
                          {isOpen ? <ChevronDown className="h-3.5 w-3.5 shrink-0 text-muted-foreground" /> : <ChevronRight className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />}
                        </button>
                        {isOpen && (
                          <div className="space-y-2 border-t border-border/60 p-2.5">
                            {s.error_message && (
                              <p className="text-xs text-red-500">{s.error_message}</p>
                            )}
                            <div>
                              <div className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Input</div>
                              <pre className="max-h-40 overflow-auto rounded-md bg-secondary/40 p-2 text-[11px]">{JSON.stringify(s.raw?.input ?? {}, null, 2)}</pre>
                            </div>
                            <div>
                              <div className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Output / response</div>
                              <pre className="max-h-40 overflow-auto rounded-md bg-secondary/40 p-2 text-[11px]">{JSON.stringify(s.raw?.output ?? {}, null, 2)}</pre>
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })
                )}
              </TabsContent>

              <TabsContent value="timeline" className="mt-5">
                {logs.length === 0 ? (
                  <div className="text-sm text-muted-foreground">No timeline events.</div>
                ) : (
                  <ol className="relative space-y-4 border-l border-border pl-5">
                    {logs.map((log, i) => {
                      const dotColor = NODE_STATUS_COLORS[log.status] || "bg-primary";
                      const duration = log.output?.duration_ms ? `${log.output.duration_ms}ms` : null;
                      return (
                        <li key={log.id || i} className="relative">
                          <span className={`absolute -left-[26px] top-1 flex h-3 w-3 items-center justify-center rounded-full border-2 border-background ${dotColor}`} />
                          <div className="text-xs text-muted-foreground">{formatDateTimeSeconds(log.executed_at || log.created_at)}</div>
                          <p className="flex items-center gap-1.5 text-sm font-medium">
                            {log.node_id}
                            {log.status && (
                              <Badge variant="outline" className="text-[10px] capitalize">{log.status}</Badge>
                            )}
                            {duration && (
                              <span className="text-[10px] text-muted-foreground">{duration}</span>
                            )}
                          </p>
                          {log.error_message && (
                            <p className="mt-0.5 text-xs text-red-500">{log.error_message}</p>
                          )}
                        </li>
                      );
                    })}
                  </ol>
                )}
              </TabsContent>

              <TabsContent value="communication" className="mt-5">
                <CommunicationTimeline events={communicationEvents} />
              </TabsContent>

              <TabsContent value="raw" className="mt-5">
                <pre className="max-h-[400px] overflow-auto rounded-lg border border-border bg-card p-3 text-xs">
                  {JSON.stringify({ instance, logs, communicationEvents }, null, 2)}
                </pre>
              </TabsContent>
            </Tabs>
          </>
        )}
      </SheetContent>
    </Sheet>
  );
}

function MetaRow({ label, value }) {
  return (
    <div className="flex items-center justify-between border-b border-border/60 pb-2 text-sm">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}

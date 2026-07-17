import { useState, useEffect, useCallback, useMemo } from "react";
import { Link } from "react-router-dom";
import { isToday } from "date-fns";
import PageHeader from "@/components/PageHeader";
import StatCard from "@/components/StatCard";
import ChartCard from "@/components/ChartCard";
import EmptyState from "@/components/EmptyState";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { communicationEventService } from "@/services/communicationEvents";
import { runningInstanceService } from "@/services/runningInstances";
import { whatsappTemplateService } from "@/services/whatsappTemplates";
import { useConversations, previewFor, ChannelBadge } from "@/modules/inbox";
import { formatRelative } from "@/lib/dateFormat";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Eye,
  Mail,
  Megaphone,
  MessageCircle,
  MessageSquare,
  Reply,
  RefreshCw,
  Send,
  Workflow,
  Zap,
} from "lucide-react";

const EVENT_ICON = {
  whatsapp_sent: MessageCircle,
  email_sent: Mail,
  replied: Reply,
  delivered: CheckCircle2,
  read: Eye,
  failed: AlertTriangle,
  journey_started: Zap,
};

export default function Dashboard() {
  const { conversations, loading: conversationsLoading, refetch: refetchConversations } = useConversations();

  const [events, setEvents] = useState([]);
  const [instances, setInstances] = useState([]);
  const [pendingTemplates, setPendingTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lastLoadedAt, setLastLoadedAt] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    const [eventsResult, instancesResult, templatesResult] = await Promise.allSettled([
      communicationEventService.list({ limit: 500 }),
      runningInstanceService.list({ limit: 200 }),
      whatsappTemplateService.list({ status: "PENDING" }),
    ]);
    setEvents(eventsResult.status === "fulfilled" ? eventsResult.value : []);
    setInstances(instancesResult.status === "fulfilled" ? instancesResult.value : []);
    setPendingTemplates(templatesResult.status === "fulfilled" ? templatesResult.value : []);
    setLastLoadedAt(new Date().toISOString());
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const metrics = useMemo(() => {
    const sentEvents = events.filter((e) => e.event_type === "whatsapp_sent" || e.event_type === "email_sent");
    const todaysSent = sentEvents.filter((e) => e.occurred_at && isToday(new Date(e.occurred_at)));
    const todaysReplied = events.filter((e) => e.event_type === "replied" && e.occurred_at && isToday(new Date(e.occurred_at)));
    const whatsappSentToday = todaysSent.filter((e) => e.channel === "whatsapp").length;
    const emailsSentToday = todaysSent.filter((e) => e.channel === "email").length;
    const todaysMessages = todaysSent.length + todaysReplied.length;

    const deliveredCount = events.filter((e) => e.event_type === "delivered").length;
    const readCount = events.filter((e) => e.event_type === "read").length;
    const repliedCount = events.filter((e) => e.event_type === "replied").length;
    const failedEvents = events.filter((e) => e.event_type === "failed");
    const failedToday = failedEvents.filter((e) => e.occurred_at && isToday(new Date(e.occurred_at))).length;
    const sentCount = sentEvents.length;

    const runningJourneys = instances.filter((i) => i.status === "running").length;
    const completedInstances = instances.filter((i) => i.status === "completed").length;
    const failedInstances = instances.filter((i) => i.status === "failed").length;
    const resolvedInstances = completedInstances + failedInstances;

    const activeConversations = conversations.filter((c) => {
      if (!c.lastActivityAt) return false;
      const days = (Date.now() - new Date(c.lastActivityAt).getTime()) / 86400000;
      return days <= 7;
    }).length;

    return {
      activeConversations,
      totalConversations: conversations.length,
      todaysMessages,
      whatsappSentToday,
      emailsSentToday,
      runningJourneys,
      automationSuccessRate: resolvedInstances > 0 ? Math.round((completedInstances / resolvedInstances) * 100) : null,
      deliveryRate: sentCount > 0 ? Math.round((deliveredCount / sentCount) * 100) : null,
      readRate: deliveredCount > 0 ? Math.round((readCount / deliveredCount) * 100) : null,
      replyRate: sentCount > 0 ? Math.round((repliedCount / sentCount) * 100) : null,
      failedToday,
      failedEvents: [...failedEvents].sort((a, b) => new Date(b.occurred_at) - new Date(a.occurred_at)).slice(0, 5),
      sentCount,
      templatesPendingApproval: pendingTemplates.length,
    };
  }, [events, instances, conversations, pendingTemplates]);

  const recentActivity = useMemo(
    () => [...events].sort((a, b) => new Date(b.occurred_at) - new Date(a.occurred_at)).slice(0, 8),
    [events]
  );

  const recentConversations = useMemo(
    () => [...conversations].sort((a, b) => new Date(b.lastActivityAt) - new Date(a.lastActivityAt)).slice(0, 5),
    [conversations]
  );

  const isLoading = loading || conversationsLoading;

  return (
    <div data-testid="page-dashboard">
      <PageHeader
        title="Command Center"
        description="Live operations across every channel, campaign and automation."
        actions={
          <>
            {lastLoadedAt && (
              <span className="hidden text-[11px] text-muted-foreground sm:inline">
                Updated {formatRelative(lastLoadedAt)}
              </span>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={() => { load(); refetchConversations(); }}
              disabled={isLoading}
              data-testid="dashboard-refresh"
            >
              <RefreshCw className={`mr-2 h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`} /> Refresh
            </Button>
          </>
        }
      />

      <div className="space-y-6 px-4 py-6 md:px-8">
        {/* KPI grid */}
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4 xl:grid-cols-4">
          <StatCard
            label="Active Conversations"
            value={metrics.activeConversations}
            hint={`${metrics.totalConversations} total`}
            icon={MessageSquare}
            testId="stat-active-conversations"
          />
          <StatCard label="Today's Messages" value={metrics.todaysMessages} icon={Send} testId="stat-todays-messages" />
          <StatCard label="WhatsApp Sent Today" value={metrics.whatsappSentToday} icon={MessageCircle} testId="stat-whatsapp-today" />
          <StatCard label="Emails Sent Today" value={metrics.emailsSentToday} icon={Mail} testId="stat-emails-today" />
          <StatCard
            label="Campaigns Running"
            value="—"
            hint="No campaign engine wired yet"
            icon={Megaphone}
            testId="stat-campaigns-running"
          />
          <StatCard label="Journeys Running" value={metrics.runningJourneys} icon={Workflow} testId="stat-journeys-running" />
          <StatCard
            label="Automation Success Rate"
            value={metrics.automationSuccessRate != null ? `${metrics.automationSuccessRate}%` : "—"}
            hint="completed vs. failed instances"
            icon={CheckCircle2}
            testId="stat-automation-success"
          />
          <StatCard
            label="Failed Messages"
            value={metrics.failedToday}
            hint="today"
            icon={AlertTriangle}
            testId="stat-failed-messages"
          />
          <StatCard
            label="Delivery Rate"
            value={metrics.deliveryRate != null ? `${metrics.deliveryRate}%` : "—"}
            hint={`of ${metrics.sentCount} sent (recent)`}
            icon={CheckCircle2}
            testId="stat-delivery-rate"
          />
          <StatCard
            label="Read Rate"
            value={metrics.readRate != null ? `${metrics.readRate}%` : "—"}
            hint="of delivered (recent)"
            icon={Eye}
            testId="stat-read-rate"
          />
          <StatCard
            label="Reply Rate"
            value={metrics.replyRate != null ? `${metrics.replyRate}%` : "—"}
            hint="of sent (recent)"
            icon={Reply}
            testId="stat-reply-rate"
          />
          <StatCard
            label="Templates Pending Approval"
            value={metrics.templatesPendingApproval}
            hint="WhatsApp · awaiting Meta review"
            icon={Activity}
            testId="stat-templates-pending"
          />
        </div>

        {/* Failed messages */}
        {metrics.failedEvents.length > 0 && (
          <ChartCard
            title="Failed messages"
            description="Most recent send failures"
            action={<span className="text-xs font-semibold text-rose-600 dark:text-rose-400">{metrics.failedEvents.length}</span>}
            testId="failed-messages"
          >
            <ul className="-mx-2 divide-y divide-border">
              {metrics.failedEvents.map((f) => (
                <li key={f.id} className="flex items-start gap-3 px-2 py-2.5">
                  <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-rose-500" />
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-medium">Lead #{f.lead_id} · {f.channel}</div>
                    <div className="truncate text-[11px] text-muted-foreground">{f.payload?.error || "Send failed"}</div>
                  </div>
                  <span className="shrink-0 text-[10px] text-muted-foreground">{formatRelative(f.occurred_at)}</span>
                </li>
              ))}
            </ul>
          </ChartCard>
        )}

        {/* Recent activity + Recent conversations */}
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <ChartCard title="Recent activity" description="Latest communication events" testId="recent-activity">
            {recentActivity.length === 0 ? (
              <EmptyState icon={Activity} title="No activity yet" description="Communication events will appear here as they happen." />
            ) : (
              <div className="-mx-2 divide-y divide-border">
                {recentActivity.map((e) => {
                  const Icon = EVENT_ICON[e.event_type] || Activity;
                  return (
                    <div key={e.id} className="flex items-start gap-3 px-2 py-2.5">
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                        <Icon className="h-3.5 w-3.5" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-sm leading-snug">
                          <span className="font-semibold">Lead #{e.lead_id}</span>{" "}
                          <span className="text-muted-foreground">{previewFor(e)}</span>
                        </p>
                        <div className="mt-0.5 flex items-center gap-2 text-xs text-muted-foreground">
                          {e.channel && e.channel !== "system" && <ChannelBadge channel={e.channel} />}
                          <span>{formatRelative(e.occurred_at)}</span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </ChartCard>

          <ChartCard title="Recent conversations" description="Most recently active leads" testId="recent-conversations">
            {recentConversations.length === 0 ? (
              <EmptyState icon={MessageSquare} title="No conversations yet" description="Conversations will appear here once a lead has any communication activity." />
            ) : (
              <div className="-mx-2 divide-y divide-border">
                {recentConversations.map((c) => (
                  <Link
                    key={c.leadId}
                    to={`/leads/${c.leadId}`}
                    className="flex items-center gap-3 px-2 py-2.5 transition-colors hover:bg-secondary/50"
                    data-testid={`dashboard-conv-${c.leadId}`}
                  >
                    <Avatar className="h-8 w-8">
                      <AvatarFallback className="bg-primary/10 text-[11px] font-semibold text-primary">
                        {String(c.leadId).slice(0, 2)}
                      </AvatarFallback>
                    </Avatar>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-2">
                        <span className="truncate text-sm font-semibold">Lead #{c.leadId}</span>
                        <span className="shrink-0 text-[11px] text-muted-foreground">{formatRelative(c.lastActivityAt)}</span>
                      </div>
                      <p className="mt-0.5 line-clamp-1 text-xs text-muted-foreground">{previewFor(c.latestEvent)}</p>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </ChartCard>
        </div>
      </div>
    </div>
  );
}

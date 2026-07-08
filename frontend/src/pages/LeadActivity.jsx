import { useState, useEffect, useMemo, useCallback } from "react";
import { useParams } from "react-router-dom";
import PageHeader from "@/components/PageHeader";
import { Card } from "@/components/ui/card";
import LoadingSkeleton from "@/components/LoadingSkeleton";
import {
  RunningInstances,
  ExecutionDrawer,
  CommunicationTimeline,
} from "@/modules/journeys";
import {
  LeadDetailsCard,
  JourneyStatusSummary,
  LeadNotesList,
  LeadTasksList,
  AIAssistantPanel,
  AISummaryCard,
  useLeadActivity,
} from "@/modules/leads";
import { journeyService } from "@/services/journeys";

/**
 * Lead Activity page — a single view combining Lead Details, Journey
 * Status, Activity Timeline, Running Journeys, Tasks, and Notes for one
 * lead. Every section is composed from existing, unmodified components and
 * APIs:
 *   - RunningInstances / ExecutionDrawer  (Journey Monitor's own components — not rebuilt)
 *   - CommunicationTimeline               (shared, unmodified — same component ExecutionDrawer uses)
 *   - GET /api/running-instances, /api/communication-events, /api/tasks/{id} (all existing)
 *
 * No backend changes, no JAWIS changes, no new endpoints.
 */
export default function LeadActivity() {
  const { leadId: leadIdParam } = useParams();
  const leadId = Number(leadIdParam);

  const { instances, events, tasks, loading, refetch } = useLeadActivity(leadId);
  const [journeyMap, setJourneyMap] = useState({});
  const [selectedInstanceId, setSelectedInstanceId] = useState(null);

  useEffect(() => {
    journeyService
      .list()
      .then((list) => setJourneyMap(Object.fromEntries(list.map((j) => [j.id, j]))))
      .catch(() => setJourneyMap({}));
  }, []);

  const lastActivityAt = useMemo(() => {
    if (events.length === 0) return null;
    return events.reduce((latest, e) => (!latest || e.occurred_at > latest ? e.occurred_at : latest), null);
  }, [events]);

  const openInstance = useCallback((id) => setSelectedInstanceId(id), []);

  if (loading && instances.length === 0 && events.length === 0) {
    return (
      <div data-testid="page-lead-activity" className="flex h-full min-h-0 flex-col">
        <PageHeader title={`Lead #${leadIdParam}`} description="Loading activity…" />
        <div className="flex-1 overflow-y-auto scrollbar-thin px-4 py-6 md:px-8">
          <LoadingSkeleton rows={5} />
        </div>
      </div>
    );
  }

  return (
    <div data-testid="page-lead-activity" className="flex h-full min-h-0 flex-col">
      <PageHeader
        title={`Lead #${leadIdParam}`}
        description={`${instances.length} journey${instances.length === 1 ? "" : "s"} · ${events.length} communication event${events.length === 1 ? "" : "s"}`}
      />

      <div className="flex-1 overflow-y-auto scrollbar-thin px-4 py-6 md:px-8">
        <div className="grid gap-4 lg:grid-cols-3">
          <LeadDetailsCard
            leadId={leadIdParam}
            instanceCount={instances.length}
            eventCount={events.length}
            lastActivityAt={lastActivityAt}
          />
          <div className="lg:col-span-2">
            <JourneyStatusSummary instances={instances} />
          </div>
        </div>

        <section className="mt-8 grid gap-4 lg:grid-cols-2">
          <AISummaryCard leadId={leadId} />
          <AIAssistantPanel leadId={leadId} />
        </section>

        <section className="mt-8">
          <h3 className="mb-3 text-lg font-bold">Running Journeys</h3>
          <RunningInstances instances={instances} journeyMap={journeyMap} onRefresh={refetch} />
        </section>

        <section className="mt-8">
          <h3 className="mb-3 text-lg font-bold">Activity Timeline</h3>
          <Card className="rounded-xl border-border bg-card p-5">
            <CommunicationTimeline events={events} />
          </Card>
        </section>

        <div className="mt-8 grid gap-6 lg:grid-cols-2">
          <section>
            <h3 className="mb-3 text-lg font-bold">Tasks</h3>
            <LeadTasksList tasks={tasks} onOpenInstance={openInstance} />
          </section>
          <section>
            <h3 className="mb-3 text-lg font-bold">Notes</h3>
            <LeadNotesList events={events} onOpenInstance={openInstance} />
          </section>
        </div>
      </div>

      <ExecutionDrawer
        instanceId={selectedInstanceId}
        onClose={() => setSelectedInstanceId(null)}
        onActionComplete={refetch}
      />
    </div>
  );
}

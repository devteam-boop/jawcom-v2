import { useMemo } from "react";
import StatCard from "@/components/StatCard";
import { Workflow, Clock, CheckCircle2, XCircle } from "lucide-react";

const WAITING_STATUSES = new Set(["waiting", "waiting_approval", "waiting_task"]);

/**
 * Journey Status summary — counts derived from the same running-instance
 * list used by the "Running Journeys" table below it. No separate fetch,
 * no new API; purely a client-side aggregate view.
 */
export default function JourneyStatusSummary({ instances = [] }) {
  const counts = useMemo(() => {
    const c = { running: 0, waiting: 0, completed: 0, failed: 0 };
    instances.forEach((inst) => {
      if (inst.status === "running") c.running += 1;
      else if (WAITING_STATUSES.has(inst.status)) c.waiting += 1;
      else if (inst.status === "completed") c.completed += 1;
      else if (inst.status === "failed") c.failed += 1;
    });
    return c;
  }, [instances]);

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      <StatCard label="Running" value={counts.running} icon={Workflow} testId="lead-status-running" />
      <StatCard label="Waiting" value={counts.waiting} icon={Clock} testId="lead-status-waiting" />
      <StatCard label="Completed" value={counts.completed} icon={CheckCircle2} testId="lead-status-completed" />
      <StatCard label="Failed" value={counts.failed} icon={XCircle} testId="lead-status-failed" />
    </div>
  );
}

import StatCard from "@/components/StatCard";
import ChartCard from "@/components/ChartCard";
import { Activity, Users, CheckCircle2, AlertTriangle, Clock } from "lucide-react";

export default function JourneyDashboard({ journey, instances = [] }) {
  const running = instances.filter((i) => i.status === "running").length;
  const completed = instances.filter((i) => i.status === "completed").length;
  const failed = instances.filter((i) => i.status === "failed").length;
  const waiting = instances.filter((i) => i.status === "waiting").length;

  const health = instances.length > 0
    ? Math.round((completed / instances.length) * 100)
    : 0;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
        <StatCard label="Running" value={running} icon={Activity} />
        <StatCard label="Completed" value={completed} icon={CheckCircle2} />
        <StatCard label="Waiting" value={waiting} icon={Clock} />
        <StatCard label="Failed" value={failed} icon={AlertTriangle} />
        <StatCard label="Health" value={`${health}%`} icon={Users} />
      </div>

      <ChartCard title="Recent Activity" description="Latest instance events">
        <div className="text-sm text-muted-foreground">
          {instances.length === 0 ? "No running instances yet." : `${instances.length} total instances`}
        </div>
      </ChartCard>
    </div>
  );
}

import ChartCard from "@/components/ChartCard";
import StatCard from "@/components/StatCard";
import { Activity, CheckCircle2, AlertTriangle, Clock, Users } from "lucide-react";

export default function JourneyAnalytics() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
        <StatCard label="Completion Rate" value="78%" icon={CheckCircle2} />
        <StatCard label="Avg Duration" value="3.2d" icon={Clock} />
        <StatCard label="Active Instances" value="142" icon={Activity} />
        <StatCard label="Failed Nodes" value="12" icon={AlertTriangle} />
        <StatCard label="Total Leads" value="1,284" icon={Users} />
      </div>

      <ChartCard title="Journey Performance" description="Completion rates over time">
        <div className="text-sm text-muted-foreground">Journey analytics chart will appear here.</div>
      </ChartCard>
    </div>
  );
}

import ChartCard from "@/components/ChartCard";
import StatCard from "@/components/StatCard";
import { Send, CheckCircle2, Eye, Reply, AlertTriangle } from "lucide-react";

export default function DeliveryReport() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
        <StatCard label="Total Sent" value="12,480" icon={Send} />
        <StatCard label="Delivered" value="11,980" icon={CheckCircle2} />
        <StatCard label="Read" value="8,420" icon={Eye} />
        <StatCard label="Replies" value="2,140" icon={Reply} />
        <StatCard label="Failed" value="500" icon={AlertTriangle} />
      </div>

      <ChartCard title="Delivery by Channel" description="Sent, delivered, read, replied">
        <div className="text-sm text-muted-foreground">Channel delivery breakdown will appear here.</div>
      </ChartCard>
    </div>
  );
}

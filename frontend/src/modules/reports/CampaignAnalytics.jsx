import ChartCard from "@/components/ChartCard";
import StatCard from "@/components/StatCard";
import { Send, Eye, Reply, MousePointerClick, TrendingUp } from "lucide-react";

export default function CampaignAnalytics() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
        <StatCard label="Total Sent" value="8,240" icon={Send} />
        <StatCard label="Open Rate" value="68%" icon={Eye} />
        <StatCard label="Reply Rate" value="18%" icon={Reply} />
        <StatCard label="CTR" value="14.5%" icon={MousePointerClick} />
        <StatCard label="Conversion" value="8.2%" icon={TrendingUp} />
      </div>

      <ChartCard title="Campaign Funnel" description="Delivery → Open → Reply → Conversion">
        <div className="text-sm text-muted-foreground">Campaign analytics funnel chart will appear here.</div>
      </ChartCard>
    </div>
  );
}

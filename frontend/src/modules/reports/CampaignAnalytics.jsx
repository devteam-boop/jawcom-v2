import EmptyState from "@/components/EmptyState";
import { TrendingUp } from "lucide-react";

/**
 * reportService.campaignAnalytics() targets /api/reports/campaigns/{id},
 * which has no backend router — and there is no campaign engine at all yet
 * (see Campaigns.jsx). This stays an empty state until both exist.
 */
export default function CampaignAnalytics() {
  return (
    <EmptyState
      icon={TrendingUp}
      title="No campaign analytics API yet"
      description="/api/reports/campaigns does not exist on the backend yet, and there is no campaign engine to report on either. Phase 2/3 work."
    />
  );
}

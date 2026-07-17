import EmptyState from "@/components/EmptyState";
import { Activity } from "lucide-react";

/**
 * reportService.journeyAnalytics() targets /api/reports/journeys/{id},
 * which has no backend router. Per-journey execution metrics (completion
 * rate, avg duration, running/failed counts) already exist as a live
 * component — see JourneyDashboard.jsx (rendered from Journey Monitor ->
 * a journey's detail page), which computes them client-side from real
 * running-instance data. A dedicated cross-journey analytics API is
 * Phase 2/3 work.
 */
export default function JourneyAnalytics() {
  return (
    <EmptyState
      icon={Activity}
      title="No journey analytics API yet"
      description="/api/reports/journeys does not exist on the backend yet. Per-journey execution metrics are available today on each journey's own detail page."
    />
  );
}

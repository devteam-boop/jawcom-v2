import EmptyState from "@/components/EmptyState";
import { Send } from "lucide-react";

/**
 * reportService.delivery() targets /api/reports/delivery, which has no
 * backend router (no app/api/report_routes.py, nothing registered in
 * main.py). Real delivery/read/reply/failed counts already exist and are
 * derivable from GET /api/communication-events, but building that
 * aggregation is a Phase 2/3 reports API, not a Phase 1 foundation fix —
 * flagged here rather than faked. Dashboard.jsx computes an equivalent
 * (approximate, recent-window) delivery/read/reply rate client-side in the
 * meantime.
 */
export default function DeliveryReport() {
  return (
    <EmptyState
      icon={Send}
      title="No delivery reporting API yet"
      description="/api/reports/delivery does not exist on the backend yet. See the Dashboard for an approximate delivery/read/reply rate computed from recent communication events."
    />
  );
}

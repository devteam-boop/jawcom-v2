import DataTable from "@/components/DataTable";
import StatusBadge from "@/components/StatusBadge";
import { Button } from "@/components/ui/button";
import { Pause, Play, XCircle } from "lucide-react";

const statusTone = {
  pending: "neutral",
  running: "info",
  waiting: "warning",
  paused: "warning",
  failed: "danger",
  completed: "success",
  cancelled: "neutral",
};

export default function RunningInstances({ instances = [] }) {
  const columns = [
    {
      key: "lead",
      label: "Lead",
      render: (r) => <span className="text-sm font-semibold">{r.leadName || r.lead_id}</span>,
    },
    {
      key: "status",
      label: "Status",
      render: (r) => <StatusBadge status={r.status} tone={statusTone[r.status]} />,
    },
    {
      key: "currentNode",
      label: "Current Node",
      render: (r) => <span className="text-xs text-muted-foreground">{r.current_node_id || "—"}</span>,
    },
    {
      key: "started",
      label: "Started",
      render: (r) => <span className="text-xs text-muted-foreground">{r.started_at || "—"}</span>,
    },
    {
      key: "actions",
      label: "",
      render: (r) => (
        <div className="flex items-center gap-1">
          {r.status === "paused" ? (
            <Button variant="ghost" size="icon" className="h-7 w-7"><Play className="h-3.5 w-3.5" /></Button>
          ) : (
            <Button variant="ghost" size="icon" className="h-7 w-7"><Pause className="h-3.5 w-3.5" /></Button>
          )}
          <Button variant="ghost" size="icon" className="h-7 w-7"><XCircle className="h-3.5 w-3.5" /></Button>
        </div>
      ),
    },
  ];

  return (
    <div>
      <DataTable columns={columns} rows={instances} testId="running-instances-table" />
    </div>
  );
}

import { useState } from "react";
import DataTable from "@/components/DataTable";
import StatusBadge from "@/components/StatusBadge";
import { Button } from "@/components/ui/button";
import { Clock, Pause, Play, XCircle } from "lucide-react";
import ExecutionDrawer from "./ExecutionDrawer";

const statusTone = {
  pending: "neutral",
  running: "info",
  waiting: "warning",
  paused: "warning",
  failed: "danger",
  completed: "success",
  cancelled: "neutral",
};

const NODE_LABEL = {
  running: "In progress",
  completed: "Done",
  waiting: "Waiting",
  paused: "Paused",
  failed: "Failed",
};

export default function RunningInstances({ instances = [], journeyMap = {}, onRefresh }) {
  const [selectedId, setSelectedId] = useState(null);

  const columns = [
    {
      key: "lead_id",
      label: "Lead ID",
      render: (r) => <span className="text-sm font-semibold">#{r.lead_id}</span>,
    },
    {
      key: "journey",
      label: "Journey",
      render: (r) => {
        const j = journeyMap[r.journey_id];
        return <span className="text-xs text-muted-foreground">{j?.name || r.journey_id || "—"}</span>;
      },
    },
    {
      key: "status",
      label: "Status",
      render: (r) => <StatusBadge status={r.status} tone={statusTone[r.status]} />,
    },
    {
      key: "currentNode",
      label: "Current Node",
      render: (r) => {
        const data = r.data || {};
        const nodeId = data.current_node_id || null;
        return (
          <span className="flex items-center gap-1 text-xs text-muted-foreground">
            {nodeId ? (
              <><Clock className="h-3 w-3" />{nodeId}</>
            ) : (
              NODE_LABEL[r.status] || "—"
            )}
          </span>
        );
      },
    },
    {
      key: "started_at",
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
      <DataTable
        columns={columns}
        rows={instances}
        onRowClick={(row) => setSelectedId(row.id)}
        testId="running-instances-table"
      />
      <ExecutionDrawer
        instanceId={selectedId}
        onClose={() => setSelectedId(null)}
        onActionComplete={onRefresh}
      />
    </div>
  );
}

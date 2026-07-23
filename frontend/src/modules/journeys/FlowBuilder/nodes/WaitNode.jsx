import { Handle, Position } from "@xyflow/react";

function summarize(config) {
  if (!config) return null;
  const waitType = config.wait_type || "duration";
  switch (waitType) {
    case "duration":
      return config.duration ? `${config.duration} ${config.unit || "days"}` : null;
    case "specific_datetime":
      return config.target_lead_field ? `until ${config.target_lead_field}` : "until a specific date/time";
    case "replied":
      return `until lead replied (${config.channel || "whatsapp"})`;
    case "stage_changed":
    case "field_condition":
      return config.field ? `until ${config.field} ${config.operator || "equals"} ${config.value || "?"}` : null;
    case "manual_approval":
      return "until manual approval";
    case "webhook_event":
      return config.event_key ? `until event '${config.event_key}'` : "until external event";
    default:
      return null;
  }
}

export default function WaitNode({ data }) {
  const summary = summarize(data.config);
  return (
    <div className="rounded-lg border border-slate-500/40 bg-slate-500/10 px-4 py-2 shadow-sm">
      <div className="flex items-center gap-2">
        <span className="text-xs font-semibold text-slate-600 dark:text-slate-400">Wait</span>
      </div>
      <div className="text-sm font-medium">{data.label}</div>
      {summary && <div className="text-[11px] text-muted-foreground">{summary}</div>}
      <Handle type="target" position={Position.Top} className="!border-slate-500 !bg-slate-500" />
      <Handle type="source" position={Position.Bottom} className="!border-slate-500 !bg-slate-500" />
    </div>
  );
}

import { Handle, Position } from "@xyflow/react";

function summarize(config) {
  if (!config) return null;
  if (config.mode === "relative_to_lead_date") {
    if (!config.lead_date_field) return null;
    const offset = config.offset_value ?? 0;
    const unit = config.offset_unit || "hours";
    return offset < 0
      ? `${Math.abs(offset)} ${unit} before ${config.lead_date_field}`
      : `${offset} ${unit} after ${config.lead_date_field}`;
  }
  if (config.duration) {
    return `${config.duration} ${config.unit || "minutes"}`;
  }
  return null;
}

export default function DelayNode({ data }) {
  const summary = summarize(data.config);
  return (
    <div className="rounded-lg border border-slate-500/40 bg-slate-500/10 px-4 py-2 shadow-sm">
      <div className="flex items-center gap-2">
        <span className="text-xs font-semibold text-slate-600 dark:text-slate-400">Delay</span>
      </div>
      <div className="text-sm font-medium">{data.label}</div>
      {summary && <div className="text-[11px] text-muted-foreground">{summary}</div>}
      <Handle type="target" position={Position.Top} className="!border-slate-500 !bg-slate-500" />
      <Handle type="source" position={Position.Bottom} className="!border-slate-500 !bg-slate-500" />
    </div>
  );
}

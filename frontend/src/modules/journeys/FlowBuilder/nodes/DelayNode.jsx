import { Handle, Position } from "@xyflow/react";

export default function DelayNode({ data }) {
  return (
    <div className="rounded-lg border border-slate-500/40 bg-slate-500/10 px-4 py-2 shadow-sm">
      <div className="flex items-center gap-2">
        <span className="text-xs font-semibold text-slate-600 dark:text-slate-400">Delay</span>
      </div>
      <div className="text-sm font-medium">{data.label}</div>
      <Handle type="target" position={Position.Top} className="!border-slate-500 !bg-slate-500" />
      <Handle type="source" position={Position.Bottom} className="!border-slate-500 !bg-slate-500" />
    </div>
  );
}

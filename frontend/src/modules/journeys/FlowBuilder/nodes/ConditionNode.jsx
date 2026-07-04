import { Handle, Position } from "@xyflow/react";

export default function ConditionNode({ data }) {
  return (
    <div className="rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-2 shadow-sm">
      <div className="flex items-center gap-2">
        <span className="text-xs font-semibold text-amber-600 dark:text-amber-400">Condition</span>
      </div>
      <div className="text-sm font-medium">{data.label}</div>
      <Handle type="target" position={Position.Top} className="!border-amber-500 !bg-amber-500" />
      <Handle type="source" position={Position.Left} id="yes" className="!border-emerald-500 !bg-emerald-500" />
      <Handle type="source" position={Position.Right} id="no" className="!border-rose-500 !bg-rose-500" />
    </div>
  );
}

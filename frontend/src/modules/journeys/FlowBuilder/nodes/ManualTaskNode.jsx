import { Handle, Position } from "@xyflow/react";

export default function ManualTaskNode({ data }) {
  return (
    <div className="rounded-lg border border-orange-500/40 bg-orange-500/10 px-4 py-2 shadow-sm">
      <div className="flex items-center gap-2">
        <span className="text-xs font-semibold text-orange-600 dark:text-orange-400">Manual Task</span>
      </div>
      <div className="text-sm font-medium">{data.label}</div>
      <Handle type="target" position={Position.Top} className="!border-orange-500 !bg-orange-500" />
      <Handle type="source" position={Position.Bottom} className="!border-orange-500 !bg-orange-500" />
    </div>
  );
}

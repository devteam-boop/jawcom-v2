import { Handle, Position } from "@xyflow/react";

export default function EndNode({ data }) {
  return (
    <div className="rounded-lg border border-rose-500/40 bg-rose-500/10 px-4 py-2 shadow-sm">
      <div className="flex items-center gap-2">
        <span className="text-xs font-semibold text-rose-600 dark:text-rose-400">End</span>
      </div>
      <div className="text-sm font-medium">{data.label}</div>
      <Handle type="target" position={Position.Top} className="!border-rose-500 !bg-rose-500" />
    </div>
  );
}

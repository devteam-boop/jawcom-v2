import { Handle, Position } from "@xyflow/react";

export default function ApprovalNode({ data }) {
  return (
    <div className="rounded-lg border border-cyan-500/40 bg-cyan-500/10 px-4 py-2 shadow-sm">
      <div className="flex items-center gap-2">
        <span className="text-xs font-semibold text-cyan-600 dark:text-cyan-400">Approval</span>
      </div>
      <div className="text-sm font-medium">{data.label}</div>
      <Handle type="target" position={Position.Top} className="!border-cyan-500 !bg-cyan-500" />
      <Handle type="source" position={Position.Bottom} className="!border-cyan-500 !bg-cyan-500" />
    </div>
  );
}

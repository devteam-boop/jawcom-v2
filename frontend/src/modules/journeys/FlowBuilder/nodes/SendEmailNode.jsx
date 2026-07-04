import { Handle, Position } from "@xyflow/react";

export default function SendEmailNode({ data }) {
  return (
    <div className="rounded-lg border border-blue-500/40 bg-blue-500/10 px-4 py-2 shadow-sm">
      <div className="flex items-center gap-2">
        <span className="text-xs font-semibold text-blue-600 dark:text-blue-400">Send Email</span>
      </div>
      <div className="text-sm font-medium">{data.label}</div>
      <Handle type="target" position={Position.Top} className="!border-blue-500 !bg-blue-500" />
      <Handle type="source" position={Position.Bottom} className="!border-blue-500 !bg-blue-500" />
    </div>
  );
}

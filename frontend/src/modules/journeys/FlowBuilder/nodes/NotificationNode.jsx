import { Handle, Position } from "@xyflow/react";

export default function NotificationNode({ data }) {
  return (
    <div className="rounded-lg border border-pink-500/40 bg-pink-500/10 px-4 py-2 shadow-sm">
      <div className="flex items-center gap-2">
        <span className="text-xs font-semibold text-pink-600 dark:text-pink-400">Notification</span>
      </div>
      <div className="text-sm font-medium">{data.label}</div>
      <Handle type="target" position={Position.Top} className="!border-pink-500 !bg-pink-500" />
      <Handle type="source" position={Position.Bottom} className="!border-pink-500 !bg-pink-500" />
    </div>
  );
}

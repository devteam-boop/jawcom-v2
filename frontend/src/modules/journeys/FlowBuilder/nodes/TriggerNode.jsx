import { Handle, Position } from "@xyflow/react";

export default function TriggerNode({ data }) {
  return (
    <div className="rounded-lg border border-indigo-500/40 bg-indigo-500/10 px-4 py-2 shadow-sm">
      <div className="flex items-center gap-2">
        <span className="text-xs font-semibold text-indigo-600 dark:text-indigo-400">Trigger</span>
      </div>
      <div className="text-sm font-medium">{data.label}</div>
      <Handle type="source" position={Position.Bottom} className="!border-indigo-500 !bg-indigo-500" />
    </div>
  );
}

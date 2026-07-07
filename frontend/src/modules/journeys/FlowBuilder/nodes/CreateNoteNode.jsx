import { Handle, Position } from "@xyflow/react";

export default function CreateNoteNode({ data }) {
  return (
    <div className="rounded-lg border border-violet-500/40 bg-violet-500/10 px-4 py-2 shadow-sm">
      <div className="flex items-center gap-2">
        <span className="text-xs font-semibold text-violet-600 dark:text-violet-400">Create Note</span>
      </div>
      <div className="text-sm font-medium">{data.label}</div>
      <Handle type="target" position={Position.Top} className="!border-violet-500 !bg-violet-500" />
      <Handle type="source" position={Position.Bottom} className="!border-violet-500 !bg-violet-500" />
    </div>
  );
}

import { Handle, Position } from "@xyflow/react";

export default function SendWhatsAppNode({ data }) {
  return (
    <div className="rounded-lg border border-emerald-500/40 bg-emerald-500/10 px-4 py-2 shadow-sm">
      <div className="flex items-center gap-2">
        <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400">Send WhatsApp</span>
      </div>
      <div className="text-sm font-medium">{data.label}</div>
      <Handle type="target" position={Position.Top} className="!border-emerald-500 !bg-emerald-500" />
      <Handle type="source" position={Position.Bottom} className="!border-emerald-500 !bg-emerald-500" />
    </div>
  );
}

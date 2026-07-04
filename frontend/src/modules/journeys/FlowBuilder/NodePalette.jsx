import { NODE_TYPES, NODE_PALETTE_ORDER } from "@/constants/flowNodes";

export default function NodePalette() {
  const onDragStart = (event, nodeType) => {
    event.dataTransfer.setData("application/reactflow", nodeType);
    event.dataTransfer.effectAllowed = "move";
  };

  return (
    <aside className="overflow-y-auto border-r border-border bg-card/40 p-3 scrollbar-thin">
      <div className="mb-2 px-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
        Nodes
      </div>
      <div className="space-y-1">
        {NODE_PALETTE_ORDER.map((key) => {
          const node = NODE_TYPES[key];
          if (!node) return null;
          const Icon = node.icon;
          return (
            <div
              key={key}
              draggable
              onDragStart={(e) => onDragStart(e, key)}
              className="flex cursor-grab items-center gap-2 rounded-lg border border-border bg-background p-2 transition-colors hover:border-primary/40"
            >
              <div className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-md border ${node.color}`}>
                <Icon className="h-3.5 w-3.5" />
              </div>
              <div className="min-w-0">
                <div className="truncate text-xs font-semibold">{node.label}</div>
              </div>
            </div>
          );
        })}
      </div>
    </aside>
  );
}

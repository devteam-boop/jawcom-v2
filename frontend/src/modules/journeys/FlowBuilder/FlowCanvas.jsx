import { useCallback, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Save, UploadCloud, CheckCircle2 } from "lucide-react";

export default function FlowCanvas({ flow, onSave, onValidate, saving }) {
  const [selectedId, setSelectedId] = useState(null);
  const canvasRef = useRef(null);

  const nodes = flow?.nodes || [];
  const edges = flow?.edges || [];

  return (
    <main className="relative overflow-auto bg-secondary/30 p-6 scrollbar-thin">
      <div
        ref={canvasRef}
        className="relative mx-auto min-h-[500px] w-full rounded-xl border border-dashed border-border bg-card"
        style={{
          backgroundImage: "radial-gradient(circle, hsl(var(--border)) 1px, transparent 1px)",
          backgroundSize: "20px 20px",
        }}
      >
        {nodes.length === 0 ? (
          <div className="flex h-full min-h-[400px] items-center justify-center text-sm text-muted-foreground">
            Drag nodes from the palette to start building your flow.
          </div>
        ) : (
          <svg className="pointer-events-none absolute inset-0 h-full w-full">
            <defs>
              <marker id="flow-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 0 0 L 10 5 L 0 10 z" fill="hsl(var(--primary))" />
              </marker>
            </defs>
          </svg>
        )}
      </div>
    </main>
  );
}

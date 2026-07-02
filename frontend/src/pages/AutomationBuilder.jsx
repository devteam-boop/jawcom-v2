<<<<<<< HEAD
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

export default function AutomationBuilder() {
  const navigate = useNavigate();
  useEffect(() => { navigate("/journeys", { replace: true }); }, [navigate]);
  return null;
=======
import { useState } from "react";
import { Link } from "react-router-dom";
import PageHeader from "@/components/PageHeader";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { NODE_PALETTE, CANVAS_NODES, CANVAS_EDGES } from "@/dummy-data/automation";
import {
  ArrowLeft,
  Zap,
  GitBranch,
  Clock,
  Sparkles,
  MessageCircle,
  Mail,
  UserPlus,
  Webhook,
  StopCircle,
  Save,
  Play,
} from "lucide-react";

const NODE_ICON = {
  Trigger: Zap,
  Condition: GitBranch,
  Delay: Clock,
  "AI Decision": Sparkles,
  "Send WhatsApp": MessageCircle,
  "Send Email": Mail,
  "Assign User": UserPlus,
  Webhook: Webhook,
  End: StopCircle,
};

const NODE_COLOR = {
  Trigger: "border-indigo-500/40 bg-indigo-500/10 text-indigo-600 dark:text-indigo-400",
  Condition: "border-amber-500/40 bg-amber-500/10 text-amber-600 dark:text-amber-400",
  Delay: "border-slate-500/40 bg-slate-500/10 text-slate-600 dark:text-slate-400",
  "AI Decision": "border-violet-500/40 bg-violet-500/10 text-violet-600 dark:text-violet-400",
  "Send WhatsApp": "border-emerald-500/40 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
  "Send Email": "border-blue-500/40 bg-blue-500/10 text-blue-600 dark:text-blue-400",
  "Assign User": "border-pink-500/40 bg-pink-500/10 text-pink-600 dark:text-pink-400",
  Webhook: "border-fuchsia-500/40 bg-fuchsia-500/10 text-fuchsia-600 dark:text-fuchsia-400",
  End: "border-rose-500/40 bg-rose-500/10 text-rose-600 dark:text-rose-400",
};

const NODE_WIDTH = 180;
const NODE_HEIGHT = 64;
const CANVAS_WIDTH = 1180;
const CANVAS_HEIGHT = 520;

export default function AutomationBuilder() {
  const [selectedId, setSelectedId] = useState("n2");
  const selected = CANVAS_NODES.find((n) => n.id === selectedId) || CANVAS_NODES[0];

  return (
    <div data-testid="page-automation-builder" className="flex h-full min-h-0 flex-col">
      <PageHeader
        title="Workflow Builder"
        description="Visual composer for your automation. (Read-only preview)"
        actions={
          <>
            <Button variant="ghost" size="sm" asChild>
              <Link to="/automation">
                <ArrowLeft className="mr-2 h-3.5 w-3.5" /> Back
              </Link>
            </Button>
            <Button variant="outline" size="sm">
              <Play className="mr-2 h-3.5 w-3.5" /> Test run
            </Button>
            <Button size="sm">
              <Save className="mr-2 h-3.5 w-3.5" /> Save draft
            </Button>
          </>
        }
      />

      <div className="grid min-h-0 flex-1 grid-cols-1 lg:grid-cols-[220px_1fr_300px]">
        {/* Palette */}
        <aside className="border-r border-border bg-card/40 p-3" data-testid="builder-palette">
          <div className="mb-2 px-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
            Nodes
          </div>
          <div className="space-y-1">
            {NODE_PALETTE.map((n) => {
              const Icon = NODE_ICON[n.type] || Zap;
              return (
                <div
                  key={n.id}
                  className="flex items-start gap-2 rounded-lg border border-border bg-background p-2 transition-colors hover:border-primary/40"
                  data-testid={`palette-${n.id}`}
                >
                  <div className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-md border ${NODE_COLOR[n.type]}`}>
                    <Icon className="h-3.5 w-3.5" />
                  </div>
                  <div className="min-w-0">
                    <div className="truncate text-xs font-semibold">{n.type}</div>
                    <div className="truncate text-[10px] text-muted-foreground">{n.description}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </aside>

        {/* Canvas */}
        <main className="overflow-auto bg-secondary/30 p-6 scrollbar-thin" data-testid="builder-canvas">
          <div
            className="relative mx-auto rounded-xl border border-dashed border-border bg-card"
            style={{
              width: CANVAS_WIDTH,
              height: CANVAS_HEIGHT,
              backgroundImage:
                "radial-gradient(circle, hsl(var(--border)) 1px, transparent 1px)",
              backgroundSize: "20px 20px",
            }}
          >
            {/* SVG edges */}
            <svg
              className="pointer-events-none absolute inset-0"
              width={CANVAS_WIDTH}
              height={CANVAS_HEIGHT}
            >
              <defs>
                <marker
                  id="arrow"
                  viewBox="0 0 10 10"
                  refX="8"
                  refY="5"
                  markerWidth="6"
                  markerHeight="6"
                  orient="auto-start-reverse"
                >
                  <path d="M 0 0 L 10 5 L 0 10 z" fill="hsl(var(--primary))" />
                </marker>
              </defs>
              {CANVAS_EDGES.map((e, i) => {
                const from = CANVAS_NODES.find((n) => n.id === e.from);
                const to = CANVAS_NODES.find((n) => n.id === e.to);
                if (!from || !to) return null;
                const x1 = from.x + NODE_WIDTH;
                const y1 = from.y + NODE_HEIGHT / 2;
                const x2 = to.x;
                const y2 = to.y + NODE_HEIGHT / 2;
                const midX = (x1 + x2) / 2;
                const d = `M ${x1} ${y1} C ${midX} ${y1}, ${midX} ${y2}, ${x2} ${y2}`;
                return (
                  <path
                    key={i}
                    d={d}
                    fill="none"
                    stroke="hsl(var(--primary))"
                    strokeWidth="1.5"
                    strokeDasharray="4 4"
                    markerEnd="url(#arrow)"
                  />
                );
              })}
            </svg>

            {/* Nodes */}
            {CANVAS_NODES.map((n) => {
              const Icon = NODE_ICON[n.type] || Zap;
              const active = n.id === selectedId;
              return (
                <button
                  key={n.id}
                  onClick={() => setSelectedId(n.id)}
                  className={`absolute flex items-center gap-2.5 rounded-xl border-2 bg-card p-2.5 text-left shadow-sm transition-all hover:shadow-md ${
                    active ? "border-primary ring-4 ring-primary/15" : "border-border"
                  }`}
                  style={{ left: n.x, top: n.y, width: NODE_WIDTH, height: NODE_HEIGHT }}
                  data-testid={`canvas-node-${n.id}`}
                >
                  <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border ${NODE_COLOR[n.type]}`}>
                    <Icon className="h-4 w-4" />
                  </div>
                  <div className="min-w-0">
                    <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">{n.type}</div>
                    <div className="truncate text-xs font-bold">{n.label}</div>
                  </div>
                </button>
              );
            })}
          </div>
        </main>

        {/* Properties */}
        <aside className="border-l border-border bg-card/40 p-5" data-testid="builder-properties">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-bold">Node properties</h3>
          </div>
          <Card className="mb-4 rounded-lg border-border bg-background p-3">
            <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Selected</div>
            <div className="mt-0.5 text-sm font-semibold">{selected.type}</div>
            <div className="text-xs text-muted-foreground">{selected.label}</div>
          </Card>

          <div className="space-y-3 text-sm">
            <div className="space-y-1.5">
              <Label>Label</Label>
              <Input defaultValue={selected.label} />
            </div>

            <div className="space-y-1.5">
              <Label>Type</Label>
              <Select defaultValue={selected.type}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {NODE_PALETTE.map((n) => (
                    <SelectItem key={n.id} value={n.type}>{n.type}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label>Description</Label>
              <Textarea rows={3} defaultValue={`Configure the ${selected.type.toLowerCase()} step here.`} />
            </div>

            <Separator />

            <div className="flex items-center justify-between rounded-lg border border-border p-2.5">
              <div>
                <div className="text-xs font-medium">Skip on error</div>
                <div className="text-[10px] text-muted-foreground">Continue if this step fails</div>
              </div>
              <Switch />
            </div>

            <div className="flex items-center justify-between rounded-lg border border-border p-2.5">
              <div>
                <div className="text-xs font-medium">Log to event stream</div>
                <div className="text-[10px] text-muted-foreground">Visible in developer events</div>
              </div>
              <Switch defaultChecked />
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
>>>>>>> 321075ad65aa3df54916ae638505753705e9661b
}

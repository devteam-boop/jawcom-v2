<<<<<<< HEAD
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

export default function Automation() {
  const navigate = useNavigate();
  useEffect(() => { navigate("/journeys", { replace: true }); }, [navigate]);
  return null;
=======
import { useState } from "react";
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
import { cn } from "@/lib/utils";
import {
  Save,
  UploadCloud,
  Play,
  Zap,
  GitBranch,
  Clock,
  Sparkles,
  MessageCircle,
  Mail,
  Phone,
  UserPlus,
  Webhook,
  StopCircle,
  Database,
  Building2,
  Timer,
  Split,
  ArrowRight,
} from "lucide-react";

// -------------------- Palette (grouped) --------------------
const PALETTE_GROUPS = [
  {
    id: "triggers",
    label: "Triggers",
    items: [
      { type: "Trigger", subtype: "Lead Stage Changed", icon: Zap },
      { type: "Trigger", subtype: "New Conversation", icon: MessageCircle },
      { type: "Trigger", subtype: "Form Submitted", icon: Database },
    ],
  },
  {
    id: "conditions",
    label: "Conditions",
    items: [
      { type: "Condition", subtype: "Reply Received?", icon: GitBranch },
      { type: "Condition", subtype: "Sentiment ≥ 0.5", icon: GitBranch },
    ],
  },
  {
    id: "communication",
    label: "Communication",
    items: [
      { type: "Communication", subtype: "Send WhatsApp", icon: MessageCircle },
      { type: "Communication", subtype: "Send Email", icon: Mail },
      { type: "Communication", subtype: "Send SMS", icon: MessageCircle },
      { type: "Communication", subtype: "Voice Call", icon: Phone },
    ],
  },
  {
    id: "ai",
    label: "AI",
    items: [
      { type: "AI", subtype: "AI Decision", icon: Sparkles },
      { type: "AI", subtype: "AI Draft Reply", icon: Sparkles },
    ],
  },
  {
    id: "wait",
    label: "Wait",
    items: [{ type: "Wait", subtype: "Wait 1 Day", icon: Timer }],
  },
  {
    id: "delay",
    label: "Delay",
    items: [
      { type: "Delay", subtype: "Delay 1 Hour", icon: Clock },
      { type: "Delay", subtype: "Delay 30 Min", icon: Clock },
    ],
  },
  {
    id: "branch",
    label: "Branch",
    items: [
      { type: "Branch", subtype: "Yes / No", icon: Split },
      { type: "Branch", subtype: "Multi-path", icon: Split },
    ],
  },
  {
    id: "crm",
    label: "CRM",
    items: [
      { type: "CRM", subtype: "Assign Sales", icon: UserPlus },
      { type: "CRM", subtype: "Update Stage", icon: Building2 },
    ],
  },
  {
    id: "integrations",
    label: "Integrations",
    items: [
      { type: "Integration", subtype: "Webhook", icon: Webhook },
      { type: "Integration", subtype: "Zapier", icon: Webhook },
    ],
  },
];

const NODE_COLOR = {
  Trigger: "border-indigo-500/40 bg-indigo-500/10 text-indigo-600 dark:text-indigo-400",
  Condition: "border-amber-500/40 bg-amber-500/10 text-amber-600 dark:text-amber-400",
  Communication: "border-emerald-500/40 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
  AI: "border-violet-500/40 bg-violet-500/10 text-violet-600 dark:text-violet-400",
  Wait: "border-slate-500/40 bg-slate-500/10 text-slate-600 dark:text-slate-400",
  Delay: "border-slate-500/40 bg-slate-500/10 text-slate-600 dark:text-slate-400",
  Branch: "border-amber-500/40 bg-amber-500/10 text-amber-600 dark:text-amber-400",
  CRM: "border-pink-500/40 bg-pink-500/10 text-pink-600 dark:text-pink-400",
  Integration: "border-fuchsia-500/40 bg-fuchsia-500/10 text-fuchsia-600 dark:text-fuchsia-400",
  End: "border-rose-500/40 bg-rose-500/10 text-rose-600 dark:text-rose-400",
};

// -------------------- Default workflow --------------------
// Layout: Lead Stage Changed → Send WhatsApp → Wait 1 Day → Reply Received?
//   YES → Assign Sales → End
//   NO  → Send Reminder → End
const NODE_WIDTH = 200;
const NODE_HEIGHT = 68;
const CANVAS_WIDTH = 1240;
const CANVAS_HEIGHT = 560;

const NODES = [
  { id: "n1", type: "Trigger", label: "Lead Stage Changed", icon: Zap, x: 40, y: 240 },
  { id: "n2", type: "Communication", label: "Send WhatsApp", icon: MessageCircle, x: 300, y: 240 },
  { id: "n3", type: "Wait", label: "Wait 1 Day", icon: Timer, x: 560, y: 240 },
  { id: "n4", type: "Condition", label: "Reply Received?", icon: GitBranch, x: 820, y: 240 },
  { id: "n5", type: "CRM", label: "Assign Sales", icon: UserPlus, x: 1080, y: 100, tag: "YES" },
  { id: "n6", type: "Communication", label: "Send Reminder", icon: MessageCircle, x: 1080, y: 380, tag: "NO" },
  { id: "n7", type: "End", label: "End", icon: StopCircle, x: 1080, y: 240 },
];

const EDGES = [
  { from: "n1", to: "n2" },
  { from: "n2", to: "n3" },
  { from: "n3", to: "n4" },
  { from: "n4", to: "n5", label: "YES" },
  { from: "n4", to: "n6", label: "NO" },
  { from: "n5", to: "n7" },
  { from: "n6", to: "n7" },
];

export default function Automation() {
  const [workflowName, setWorkflowName] = useState("Lead Nurture · Growth Plan");
  const [openGroup, setOpenGroup] = useState("triggers");
  const [selectedId, setSelectedId] = useState("n1");
  const selected = NODES.find((n) => n.id === selectedId) || NODES[0];

  return (
    <div data-testid="page-automation" className="flex h-full min-h-0 flex-col">
      {/* Top toolbar */}
      <PageHeader
        title="Automation"
        description="Visual customer journey builder"
        actions={
          <>
            <Input
              value={workflowName}
              onChange={(e) => setWorkflowName(e.target.value)}
              className="hidden h-9 w-[280px] sm:inline-flex"
              placeholder="Workflow name"
              data-testid="workflow-name"
            />
            <Button variant="outline" size="sm" data-testid="workflow-save">
              <Save className="mr-2 h-3.5 w-3.5" /> Save
            </Button>
            <Button variant="outline" size="sm" data-testid="workflow-test">
              <Play className="mr-2 h-3.5 w-3.5" /> Test
            </Button>
            <Button size="sm" data-testid="workflow-publish">
              <UploadCloud className="mr-2 h-3.5 w-3.5" /> Publish
            </Button>
          </>
        }
      />

      <div className="grid min-h-0 flex-1 grid-cols-1 lg:grid-cols-[240px_1fr_300px]">
        {/* Left palette */}
        <aside className="overflow-y-auto scrollbar-thin border-r border-border bg-card/40 p-3" data-testid="workflow-palette">
          <div className="mb-2 px-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
            Node library
          </div>
          <div className="space-y-1.5">
            {PALETTE_GROUPS.map((g) => {
              const open = openGroup === g.id;
              return (
                <div key={g.id} className="rounded-lg border border-border bg-background">
                  <button
                    onClick={() => setOpenGroup(open ? "" : g.id)}
                    className="flex w-full items-center justify-between px-2.5 py-1.5 text-left text-xs font-semibold"
                    data-testid={`palette-group-${g.id}`}
                  >
                    <span>{g.label}</span>
                    <span className="text-muted-foreground">{open ? "−" : "+"}</span>
                  </button>
                  {open && (
                    <div className="space-y-1 border-t border-border p-1.5">
                      {g.items.map((item) => {
                        const Icon = item.icon;
                        return (
                          <div
                            key={item.subtype}
                            draggable
                            className="flex cursor-grab items-center gap-2 rounded-md border border-border bg-card p-1.5 hover:border-primary/40"
                            data-testid={`palette-item-${item.subtype}`}
                          >
                            <div className={cn("flex h-6 w-6 shrink-0 items-center justify-center rounded-md border", NODE_COLOR[item.type])}>
                              <Icon className="h-3 w-3" />
                            </div>
                            <div className="min-w-0 text-[11px] font-medium">{item.subtype}</div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </aside>

        {/* Center canvas */}
        <main className="overflow-auto bg-secondary/30 p-6 scrollbar-thin" data-testid="workflow-canvas">
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
            <svg className="pointer-events-none absolute inset-0" width={CANVAS_WIDTH} height={CANVAS_HEIGHT}>
              <defs>
                <marker id="wf-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                  <path d="M 0 0 L 10 5 L 0 10 z" fill="hsl(var(--primary))" />
                </marker>
              </defs>
              {EDGES.map((e, i) => {
                const from = NODES.find((n) => n.id === e.from);
                const to = NODES.find((n) => n.id === e.to);
                if (!from || !to) return null;
                const x1 = from.x + NODE_WIDTH;
                const y1 = from.y + NODE_HEIGHT / 2;
                const x2 = to.x;
                const y2 = to.y + NODE_HEIGHT / 2;
                const midX = (x1 + x2) / 2;
                const d = `M ${x1} ${y1} C ${midX} ${y1}, ${midX} ${y2}, ${x2} ${y2}`;
                return (
                  <g key={i}>
                    <path d={d} fill="none" stroke="hsl(var(--primary))" strokeWidth="1.5" strokeDasharray="4 4" markerEnd="url(#wf-arrow)" />
                    {e.label && (
                      <foreignObject x={midX - 18} y={(y1 + y2) / 2 - 10} width={36} height={20}>
                        <div className="flex h-5 w-9 items-center justify-center rounded-full border border-border bg-background text-[10px] font-semibold">
                          {e.label}
                        </div>
                      </foreignObject>
                    )}
                  </g>
                );
              })}
            </svg>

            {NODES.map((n) => {
              const Icon = n.icon;
              const active = n.id === selectedId;
              return (
                <button
                  key={n.id}
                  onClick={() => setSelectedId(n.id)}
                  className={cn(
                    "absolute flex items-center gap-2.5 rounded-xl border-2 bg-card p-2.5 text-left shadow-sm transition-all hover:shadow-md",
                    active ? "border-primary ring-4 ring-primary/15" : "border-border"
                  )}
                  style={{ left: n.x, top: n.y, width: NODE_WIDTH, height: NODE_HEIGHT }}
                  data-testid={`wf-node-${n.id}`}
                >
                  <div className={cn("flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border", NODE_COLOR[n.type])}>
                    <Icon className="h-4 w-4" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">{n.type}</div>
                    <div className="truncate text-xs font-bold">{n.label}</div>
                  </div>
                  {n.tag && (
                    <span className="rounded-full bg-secondary px-1.5 py-0.5 text-[9px] font-bold text-muted-foreground">
                      {n.tag}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </main>

        {/* Right properties panel */}
        <aside className="overflow-y-auto scrollbar-thin border-l border-border bg-card/40 p-5" data-testid="workflow-properties">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-bold">Node settings</h3>
            <ArrowRight className="h-3.5 w-3.5 text-muted-foreground" />
          </div>
          <Card className="mb-4 rounded-lg border-border bg-background p-3">
            <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Selected</div>
            <div className="mt-0.5 text-sm font-semibold">{selected.type}</div>
            <div className="text-xs text-muted-foreground">{selected.label}</div>
          </Card>

          <div className="space-y-3 text-sm">
            <div className="space-y-1.5">
              <Label>Label</Label>
              <Input defaultValue={selected.label} key={selected.id + "-label"} />
            </div>

            <div className="space-y-1.5">
              <Label>Type</Label>
              <Select value={selected.type} disabled>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {Object.keys(NODE_COLOR).map((t) => (
                    <SelectItem key={t} value={t}>{t}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label>Description</Label>
              <Textarea
                rows={3}
                key={selected.id + "-desc"}
                defaultValue={`Configure the ${selected.type.toLowerCase()} step here.`}
              />
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

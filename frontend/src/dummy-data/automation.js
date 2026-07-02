export const WORKFLOWS = [
  { id: "wf1", name: "Welcome new signups", trigger: "User signed up", status: "Active", runs: 1284, success: 96, lastRun: "2m ago", description: "Send onboarding sequence and assign owner." },
  { id: "wf2", name: "Reactivate dormant leads", trigger: "No activity in 30 days", status: "Active", runs: 412, success: 38, lastRun: "1h ago", description: "Send re-engagement message and surface to AE." },
  { id: "wf3", name: "Proposal follow-up cadence", trigger: "Proposal sent", status: "Active", runs: 184, success: 62, lastRun: "3h ago", description: "3-touch follow-up over 7 days if no reply." },
  { id: "wf4", name: "Negative sentiment alert", trigger: "Sentiment < 0.3", status: "Active", runs: 28, success: 100, lastRun: "Yesterday", description: "Notify CSM in Slack and escalate." },
  { id: "wf5", name: "High-intent lead routing", trigger: "Intent score > 80", status: "Paused", runs: 96, success: 84, lastRun: "2d ago", description: "Auto-assign to enterprise AE." },
  { id: "wf6", name: "Renewal 30 days out", trigger: "30 days before renewal", status: "Active", runs: 64, success: 71, lastRun: "1d ago", description: "Trigger renewal nudge journey." },
  { id: "wf7", name: "Lost deal retro", trigger: "Deal marked lost", status: "Draft", runs: 0, success: 0, lastRun: "—", description: "Send retro form and AI-summarized notes." },
  { id: "wf8", name: "Webhook to billing", trigger: "Plan upgraded", status: "Active", runs: 312, success: 99, lastRun: "20m ago", description: "POST to /billing/sync." },
];

export const WORKFLOW_HISTORY = [
  { id: "h1", time: "2m ago", entity: "Priya Sharma", result: "Success", duration: "1.2s" },
  { id: "h2", time: "8m ago", entity: "Daniel Chen", result: "Success", duration: "0.9s" },
  { id: "h3", time: "14m ago", entity: "Hana Park", result: "Skipped", duration: "0.1s" },
  { id: "h4", time: "32m ago", entity: "Sofia Rossi", result: "Success", duration: "1.4s" },
  { id: "h5", time: "1h ago", entity: "Akira Tanaka", result: "Failed", duration: "2.1s" },
  { id: "h6", time: "2h ago", entity: "Lila Okafor", result: "Success", duration: "1.1s" },
];

export const NODE_PALETTE = [
  { id: "p1", type: "Trigger", color: "indigo", description: "Start the workflow" },
  { id: "p2", type: "Condition", color: "amber", description: "Branch by rule" },
  { id: "p3", type: "Delay", color: "slate", description: "Wait an interval" },
  { id: "p4", type: "AI Decision", color: "violet", description: "Let AI route" },
  { id: "p5", type: "Send WhatsApp", color: "emerald", description: "Outbound message" },
  { id: "p6", type: "Send Email", color: "blue", description: "Outbound email" },
  { id: "p7", type: "Assign User", color: "pink", description: "Route to a teammate" },
  { id: "p8", type: "Webhook", color: "fuchsia", description: "POST to URL" },
  { id: "p9", type: "End", color: "rose", description: "Finish the flow" },
];

// Pre-placed nodes with hardcoded coords on a 1100x520 canvas
export const CANVAS_NODES = [
  { id: "n1", type: "Trigger", label: "New conversation", x: 40, y: 220 },
  { id: "n2", type: "AI Decision", label: "Intent classifier", x: 260, y: 220 },
  { id: "n3", type: "Condition", label: "High intent?", x: 480, y: 90 },
  { id: "n4", type: "Condition", label: "Returning user?", x: 480, y: 350 },
  { id: "n5", type: "Send WhatsApp", label: "Send WA template", x: 720, y: 40 },
  { id: "n6", type: "Assign User", label: "Route to AE", x: 720, y: 160 },
  { id: "n7", type: "Send Email", label: "Send pricing email", x: 720, y: 300 },
  { id: "n8", type: "Delay", label: "Wait 2 days", x: 720, y: 420 },
  { id: "n9", type: "End", label: "End", x: 960, y: 230 },
];

// Edges: from node id -> to node id
export const CANVAS_EDGES = [
  { from: "n1", to: "n2" },
  { from: "n2", to: "n3" },
  { from: "n2", to: "n4" },
  { from: "n3", to: "n5" },
  { from: "n3", to: "n6" },
  { from: "n4", to: "n7" },
  { from: "n4", to: "n8" },
  { from: "n5", to: "n9" },
  { from: "n6", to: "n9" },
  { from: "n7", to: "n9" },
  { from: "n8", to: "n9" },
];

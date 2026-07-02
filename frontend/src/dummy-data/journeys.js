// Journey domain dummy data.
// NOTE: In production, `stageKey`/`stageLabel` come from JAWIS (plain strings —
// no foreign key, so JAWIS can add stages without JawCom code changes).
// Lead/company fields on RUNNING_INSTANCES are READ-ONLY snapshots that would
// be fetched live from the JAWIS API — JawCom never owns this data.

// -------------------- Stage Mapping --------------------
// stage (JAWIS) -> journey (JawCom), simplified per architecture review:
//   trigger: "enter" | "exit" | "reenter"
//   mode:    "automatic" | "manual"
export const STAGE_MAPPINGS = [
  { id: "sm1", stageKey: "qualified", stageLabel: "Qualified", journeyId: "jr1", trigger: "enter", mode: "automatic", enabled: true },
  { id: "sm2", stageKey: "demand-follow-up", stageLabel: "Demand Follow-Up", journeyId: "jr2", trigger: "enter", mode: "automatic", enabled: true },
  { id: "sm3", stageKey: "won", stageLabel: "Won", journeyId: "jr3", trigger: "enter", mode: "automatic", enabled: false },
  { id: "sm4", stageKey: "lost", stageLabel: "Lost", journeyId: "jr4", trigger: "enter", mode: "manual", enabled: true },
];

// -------------------- Journeys --------------------
export const JOURNEY_LIST = [
  {
    id: "jr1",
    name: "Lead Qualification Journey",
    stageKey: "qualified",
    stageLabel: "Qualified",
    status: "active", // active | paused | draft
    description: "Nurture a newly qualified lead toward a booked demo.",
    flowVersion: 3,
    runningCount: 142,
    health: 98,
  },
  {
    id: "jr2",
    name: "Demand Journey",
    stageKey: "demand-follow-up",
    stageLabel: "Demand Follow-Up",
    status: "active",
    description: "Follow up on open requirements and pricing questions.",
    flowVersion: 1,
    runningCount: 53,
    health: 95,
  },
  {
    id: "jr3",
    name: "Customer Success Journey",
    stageKey: "won",
    stageLabel: "Won",
    status: "draft",
    description: "Onboard and delight newly won customers.",
    flowVersion: 1,
    runningCount: 0,
    health: null,
  },
  {
    id: "jr4",
    name: "Win Back Journey",
    stageKey: "lost",
    stageLabel: "Lost",
    status: "paused",
    description: "Re-engage lost leads with a win-back offer.",
    flowVersion: 2,
    runningCount: 12,
    health: 87,
  },
];

// -------------------- Flow Definitions (one active flow per journey) --------------------
// V1 node types only: Trigger, Delay, Condition, Send WhatsApp, Send Email,
// Notification, Wait, End. No AI. No SMS. No Voice.
const NODE_W = 200;
const NODE_H = 68;

export const FLOW_DEFINITIONS = {
  jr1: {
    version: 3,
    canvasWidth: 1180,
    canvasHeight: 420,
    nodes: [
      { id: "n1", type: "trigger", label: "Stage: Qualified", x: 40, y: 176 },
      { id: "n2", type: "send_whatsapp", label: "Send Welcome Template", x: 300, y: 176, config: { templateId: "welcome_whatsapp" } },
      { id: "n3", type: "delay", label: "Wait 24 hours", x: 560, y: 176, config: { duration: 24, unit: "hours" } },
      { id: "n4", type: "condition", label: "Replied?", x: 820, y: 176, config: { field: "conversation.status", operator: "==", value: "replied" } },
      { id: "n5", type: "notification", label: "Notify Owner", x: 1080, y: 60, tag: "YES", config: { channel: "in-app", message: "Lead replied — follow up manually" } },
      { id: "n6", type: "send_email", label: "Send Follow-up Email", x: 1080, y: 290, tag: "NO", config: { templateId: "followup_email" } },
    ],
    edges: [
      { from: "n1", to: "n2" },
      { from: "n2", to: "n3" },
      { from: "n3", to: "n4" },
      { from: "n4", to: "n5", label: "YES" },
      { from: "n4", to: "n6", label: "NO" },
    ],
  },
  jr2: {
    version: 1,
    canvasWidth: 960,
    canvasHeight: 300,
    nodes: [
      { id: "n1", type: "trigger", label: "Stage: Demand Follow-Up", x: 40, y: 116 },
      { id: "n2", type: "send_email", label: "Send Requirement Recap", x: 300, y: 116, config: { templateId: "requirement_recap_email" } },
      { id: "n3", type: "wait", label: "Wait for Reply", x: 560, y: 116, config: { type: "until_event", value: "conversation.reply" } },
      { id: "n4", type: "end", label: "End", x: 800, y: 116 },
    ],
    edges: [
      { from: "n1", to: "n2" },
      { from: "n2", to: "n3" },
      { from: "n3", to: "n4" },
    ],
  },
  jr3: {
    version: 1,
    canvasWidth: 720,
    canvasHeight: 260,
    nodes: [
      { id: "n1", type: "trigger", label: "Stage: Won", x: 40, y: 96 },
      { id: "n2", type: "send_whatsapp", label: "Send Welcome Aboard", x: 300, y: 96, config: { templateId: "welcome_aboard_whatsapp" } },
      { id: "n3", type: "end", label: "End", x: 560, y: 96 },
    ],
    edges: [
      { from: "n1", to: "n2" },
      { from: "n2", to: "n3" },
    ],
  },
  jr4: {
    version: 2,
    canvasWidth: 960,
    canvasHeight: 300,
    nodes: [
      { id: "n1", type: "trigger", label: "Stage: Lost", x: 40, y: 116 },
      { id: "n2", type: "delay", label: "Wait 30 days", x: 300, y: 116, config: { duration: 30, unit: "days" } },
      { id: "n3", type: "send_email", label: "Send Win-Back Offer", x: 560, y: 116, config: { templateId: "winback_offer_email" } },
      { id: "n4", type: "end", label: "End", x: 800, y: 116 },
    ],
    edges: [
      { from: "n1", to: "n2" },
      { from: "n2", to: "n3" },
      { from: "n3", to: "n4" },
    ],
  },
};

// -------------------- Running Journey Instances --------------------
// status: pending | running | waiting | paused | failed | completed | cancelled
export const RUNNING_INSTANCES = [
  { id: "ri1", journeyId: "jr1", leadName: "Priya Sharma", company: "Lumen Studio", currentNodeId: "n3", status: "waiting", startedAt: "2026-06-30T09:00:00Z", nextExecution: "2026-07-01T09:00:00Z", lastExecution: "2026-06-30T09:00:05Z" },
  { id: "ri2", journeyId: "jr1", leadName: "Daniel Chen", company: "Northwind", currentNodeId: "n2", status: "running", startedAt: "2026-07-01T08:00:00Z", nextExecution: "2026-07-01T08:05:00Z", lastExecution: "2026-07-01T08:00:00Z" },
  { id: "ri3", journeyId: "jr1", leadName: "Sofia Rossi", company: "Atelier Rossi", currentNodeId: "n6", status: "completed", startedAt: "2026-06-25T09:00:00Z", nextExecution: null, lastExecution: "2026-06-26T09:00:10Z", completedAt: "2026-06-26T09:00:10Z" },
  { id: "ri4", journeyId: "jr1", leadName: "Akira Tanaka", company: "Kairos Labs", currentNodeId: "n2", status: "failed", startedAt: "2026-07-01T07:00:00Z", nextExecution: "2026-07-01T09:00:00Z", lastExecution: "2026-07-01T07:00:03Z" },
  { id: "ri5", journeyId: "jr2", leadName: "Hana Park", company: "Mira Foods", currentNodeId: "n3", status: "waiting", startedAt: "2026-06-29T10:00:00Z", nextExecution: null, lastExecution: "2026-06-29T10:00:04Z" },
  { id: "ri6", journeyId: "jr2", leadName: "Diego Alvarez", company: "Vela Travel", currentNodeId: "n2", status: "running", startedAt: "2026-07-01T06:00:00Z", nextExecution: "2026-07-01T06:00:00Z", lastExecution: "2026-07-01T06:00:00Z" },
  { id: "ri7", journeyId: "jr4", leadName: "Marco Bianchi", company: "Solare Group", currentNodeId: "n2", status: "paused", startedAt: "2026-06-01T09:00:00Z", nextExecution: "2026-07-01T09:00:00Z", lastExecution: "2026-06-01T09:00:00Z" },
  { id: "ri8", journeyId: "jr4", leadName: "Nour Haddad", company: "Orbit Retail", currentNodeId: "n3", status: "running", startedAt: "2026-06-05T09:00:00Z", nextExecution: "2026-07-05T09:00:00Z", lastExecution: "2026-06-05T09:00:00Z" },
];

export const JAWIS_SYNC_STATUS = {
  connected: true,
  lastSync: "2m ago",
};

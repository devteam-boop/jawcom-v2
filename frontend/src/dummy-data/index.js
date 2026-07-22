// Centralized dummy data for JawCom - frontend-only static SaaS shell

export const WORKSPACES = [
  { id: "ws-1", name: "JawCom HQ", plan: "Growth" },
  { id: "ws-2", name: "Acme Sales Team", plan: "Pro" },
  { id: "ws-3", name: "Helio Marketing", plan: "Starter" },
];

export const CURRENT_USER = {
  name: "Maya Iyer",
  email: "maya@jawcom.io",
  role: "Workspace Admin",
  initials: "MI",
};

export const KPIS = [
  { key: "today_convos", label: "Today's Conversations", value: 284, delta: 12.4, trend: "up", hint: "vs yesterday" },
  { key: "new_leads", label: "New Leads", value: 47, delta: 8.1, trend: "up", hint: "this week" },
  { key: "pending_followups", label: "Pending Follow-ups", value: 23, delta: -3.2, trend: "down", hint: "due today" },
  { key: "messages_sent", label: "Messages Sent", value: 1248, delta: 18.6, trend: "up", hint: "last 24h" },
  { key: "replies", label: "Replies Received", value: 612, delta: 5.7, trend: "up", hint: "reply rate 49%" },
  { key: "tasks_due", label: "Tasks Due", value: 14, delta: 0, trend: "flat", hint: "today" },
];

export const MESSAGES_CHART = [
  { day: "Mon", sent: 180, received: 92 },
  { day: "Tue", sent: 220, received: 121 },
  { day: "Wed", sent: 198, received: 104 },
  { day: "Thu", sent: 264, received: 142 },
  { day: "Fri", sent: 312, received: 178 },
  { day: "Sat", sent: 142, received: 67 },
  { day: "Sun", sent: 98, received: 48 },
];

export const LEADS_CHART = [
  { week: "W1", leads: 32, qualified: 12 },
  { week: "W2", leads: 41, qualified: 18 },
  { week: "W3", leads: 38, qualified: 14 },
  { week: "W4", leads: 54, qualified: 24 },
  { week: "W5", leads: 47, qualified: 21 },
  { week: "W6", leads: 61, qualified: 29 },
];

export const REPLY_RATE_CHART = [
  { month: "Sep", rate: 38 },
  { month: "Oct", rate: 42 },
  { month: "Nov", rate: 41 },
  { month: "Dec", rate: 46 },
  { month: "Jan", rate: 49 },
  { month: "Feb", rate: 52 },
];

export const CONVERSION_CHART = [
  { stage: "Visited", value: 1248 },
  { stage: "Engaged", value: 612 },
  { stage: "Qualified", value: 284 },
  { stage: "Proposal", value: 124 },
  { stage: "Won", value: 47 },
];

export const RECENT_ACTIVITY = [
  { id: "a1", actor: "Rohan Mehta", action: "replied to", target: "Priya Sharma", time: "2m ago", channel: "WhatsApp" },
  { id: "a2", actor: "AI Assistant", action: "drafted reply for", target: "Daniel Chen", time: "5m ago", channel: "Email" },
  { id: "a3", actor: "Maya Iyer", action: "closed conversation with", target: "Sofia Rossi", time: "12m ago", channel: "Instagram" },
  { id: "a4", actor: "Campaign: Spring Promo", action: "sent to", target: "248 contacts", time: "28m ago", channel: "WhatsApp" },
  { id: "a5", actor: "Journey: Welcome", action: "completed for", target: "Akira Tanaka", time: "1h ago", channel: "Email" },
  { id: "a6", actor: "Rohan Mehta", action: "assigned", target: "Lila Okafor", time: "2h ago", channel: "Facebook" },
];

export const UPCOMING_FOLLOWUPS = [
  { id: "f1", customer: "Priya Sharma", company: "Lumen Studio", action: "Send proposal", due: "Today, 3:00 PM", channel: "Email", priority: "high" },
  { id: "f2", customer: "Daniel Chen", company: "Northwind", action: "Demo call", due: "Today, 4:30 PM", channel: "Call", priority: "high" },
  { id: "f3", customer: "Sofia Rossi", company: "Atelier Rossi", action: "Check-in", due: "Tomorrow, 11:00 AM", channel: "WhatsApp", priority: "medium" },
  { id: "f4", customer: "Akira Tanaka", company: "Kairos Labs", action: "Send pricing", due: "Tomorrow, 2:00 PM", channel: "Email", priority: "medium" },
  { id: "f5", customer: "Lila Okafor", company: "Bloom & Co", action: "Renewal reminder", due: "Fri, 10:00 AM", channel: "Email", priority: "low" },
];

const channels = ["WhatsApp", "Email", "Instagram", "Facebook", "SMS"];
const statuses = ["Unread", "Open", "Closed", "Assigned"];
const stages = ["New", "Qualified", "Proposal", "Negotiation", "Won", "Lost"];

export const CUSTOMERS = Array.from({ length: 24 }).map((_, i) => {
  const names = [
    "Priya Sharma", "Daniel Chen", "Sofia Rossi", "Akira Tanaka", "Lila Okafor",
    "Marco Bianchi", "Hana Park", "Diego Alvarez", "Nour Haddad", "Yuki Sato",
    "Olivia Bennett", "Kabir Singh", "Ines Costa", "Tomás Pereira", "Mei Lin",
    "Jonas Weber", "Amara Diallo", "Ravi Iyer", "Elena Petrova", "Lucas Martin",
    "Aisha Khan", "Felix Müller", "Camila Reyes", "Theo Andersen",
  ];
  const companies = [
    "Lumen Studio", "Northwind", "Atelier Rossi", "Kairos Labs", "Bloom & Co",
    "Solare Group", "Mira Foods", "Vela Travel", "Cedar Health", "Orbit Retail",
    "Pixel Forge", "Helio Marketing", "Nimbus Cloud", "Stratus IO", "Aster Bank",
    "Vanta Co", "Ember & Oak", "Brio Logistics", "Aurora AI", "Mosaic Studio",
    "Lattice Labs", "Quill Press", "Tiller Capital", "Cobalt Co",
  ];
  return {
    id: `cu-${i + 1}`,
    name: names[i],
    initials: names[i].split(" ").map((n) => n[0]).join(""),
    company: companies[i],
    email: names[i].toLowerCase().replace(/\s+/g, ".") + "@" + companies[i].toLowerCase().replace(/[^a-z]/g, "") + ".com",
    status: ["Active", "Active", "Inactive", "Active", "Lead"][i % 5],
    stage: stages[i % stages.length],
    owner: ["Maya Iyer", "Rohan Mehta", "Ana Souza", "Kenji Watanabe"][i % 4],
    lastContact: ["Today", "Yesterday", "2 days ago", "1 week ago", "Today"][i % 5],
    channel: channels[i % channels.length],
    tags: [["enterprise"], ["smb"], ["retail"], ["startup"], ["mid-market"]][i % 5],
  };
});

export const CAMPAIGNS = [
  { id: "cp1", name: "Spring Promo 2026", status: "Running", channel: "WhatsApp", audience: 2840, sent: 2400, opens: 1820, replies: 412, ctr: 14.5, schedule: "Daily · 10am IST" },
  { id: "cp2", name: "Q1 Renewal Push", status: "Running", channel: "Email", audience: 1240, sent: 1240, opens: 762, replies: 198, ctr: 16.0, schedule: "One-time" },
  { id: "cp3", name: "Demo Day Invite", status: "Scheduled", channel: "Email", audience: 540, sent: 0, opens: 0, replies: 0, ctr: 0, schedule: "Feb 18, 9am" },
  { id: "cp4", name: "Lost Lead Recovery", status: "Draft", channel: "WhatsApp", audience: 380, sent: 0, opens: 0, replies: 0, ctr: 0, schedule: "—" },
  { id: "cp5", name: "Holiday Greetings", status: "Completed", channel: "SMS", audience: 4200, sent: 4200, opens: 3120, replies: 84, ctr: 2.0, schedule: "Completed Dec 25" },
  { id: "cp6", name: "New Feature: Voice AI", status: "Completed", channel: "Email", audience: 1800, sent: 1800, opens: 1240, replies: 312, ctr: 17.3, schedule: "Completed Jan 12" },
  { id: "cp7", name: "Webinar Reminders", status: "Scheduled", channel: "WhatsApp", audience: 720, sent: 0, opens: 0, replies: 0, ctr: 0, schedule: "Feb 22, 6pm" },
  { id: "cp8", name: "VIP Outreach", status: "Draft", channel: "Email", audience: 64, sent: 0, opens: 0, replies: 0, ctr: 0, schedule: "—" },
];

export const JOURNEYS = [
  { id: "j1", name: "Welcome Series", status: "Active", messages: 4, success: 78, lastRun: "2m ago", trigger: "New signup" },
  { id: "j2", name: "Lead Qualification", status: "Active", messages: 6, success: 64, lastRun: "12m ago", trigger: "Form submit" },
  { id: "j3", name: "Visit Reminder", status: "Active", messages: 3, success: 71, lastRun: "1h ago", trigger: "Booking made" },
  { id: "j4", name: "Proposal Follow-up", status: "Active", messages: 5, success: 58, lastRun: "3h ago", trigger: "Proposal sent" },
  { id: "j5", name: "Lost Lead Recovery", status: "Paused", messages: 4, success: 22, lastRun: "Yesterday", trigger: "Deal lost" },
  { id: "j6", name: "Onboarding", status: "Active", messages: 7, success: 88, lastRun: "30m ago", trigger: "Subscription started" },
  { id: "j7", name: "Renewal", status: "Active", messages: 4, success: 67, lastRun: "1d ago", trigger: "30 days before renewal" },
  { id: "j8", name: "Referral Program", status: "Draft", messages: 3, success: 0, lastRun: "—", trigger: "NPS > 9" },
];

export const FOLLOWUPS = {
  today: [
    { id: "ft1", customer: "Priya Sharma", company: "Lumen Studio", initials: "PS", action: "Send proposal", time: "3:00 PM", channel: "Email", priority: "high", owner: "Maya Iyer" },
    { id: "ft2", customer: "Daniel Chen", company: "Northwind", initials: "DC", action: "Demo call", time: "4:30 PM", channel: "Call", priority: "high", owner: "Maya Iyer" },
    { id: "ft3", customer: "Hana Park", company: "Mira Foods", initials: "HP", action: "Pricing check-in", time: "5:15 PM", channel: "WhatsApp", priority: "medium", owner: "Rohan Mehta" },
  ],
  upcoming: [
    { id: "fu1", customer: "Sofia Rossi", company: "Atelier Rossi", initials: "SR", action: "Check-in", time: "Tomorrow · 11:00 AM", channel: "WhatsApp", priority: "medium", owner: "Rohan Mehta" },
    { id: "fu2", customer: "Akira Tanaka", company: "Kairos Labs", initials: "AT", action: "Send pricing", time: "Tomorrow · 2:00 PM", channel: "Email", priority: "medium", owner: "Maya Iyer" },
    { id: "fu3", customer: "Lila Okafor", company: "Bloom & Co", initials: "LO", action: "Renewal reminder", time: "Fri · 10:00 AM", channel: "Email", priority: "low", owner: "Maya Iyer" },
    { id: "fu4", customer: "Diego Alvarez", company: "Vela Travel", initials: "DA", action: "Q2 planning call", time: "Mon · 3:00 PM", channel: "Call", priority: "medium", owner: "Ana Souza" },
  ],
  completed: [
    { id: "fc1", customer: "Marco Bianchi", company: "Solare Group", initials: "MB", action: "Closure note", time: "Yesterday", channel: "Email", priority: "low", owner: "Maya Iyer" },
    { id: "fc2", customer: "Yuki Sato", company: "Cedar Health", initials: "YS", action: "Thank-you note", time: "2 days ago", channel: "WhatsApp", priority: "low", owner: "Rohan Mehta" },
  ],
  overdue: [
    { id: "fo1", customer: "Nour Haddad", company: "Orbit Retail", initials: "NH", action: "Send contract", time: "Overdue · 2 days", channel: "Email", priority: "high", owner: "Maya Iyer" },
    { id: "fo2", customer: "Jonas Weber", company: "Vanta Co", initials: "JW", action: "Confirm requirements", time: "Overdue · 1 day", channel: "Call", priority: "high", owner: "Ana Souza" },
  ],
};

export const INTEGRATIONS = [
  { id: "in1", name: "WhatsApp Business", category: "Channel", connected: true, accounts: 2, description: "Send and receive WhatsApp at scale." },
  { id: "in2", name: "Facebook Messenger", category: "Channel", connected: true, accounts: 1, description: "Unified Messenger inbox for your pages." },
  { id: "in3", name: "Instagram DM", category: "Channel", connected: false, accounts: 0, description: "Reply to DMs from your business profile." },
  { id: "in4", name: "Google Business", category: "Channel", connected: true, accounts: 1, description: "Handle Google Business Profile messages." },
  { id: "in5", name: "Gmail", category: "Email", connected: true, accounts: 3, description: "Sync Gmail threads bi-directionally." },
  { id: "in6", name: "Claude (Anthropic)", category: "AI", connected: true, accounts: 1, description: "Power assistant replies with Claude." },
  { id: "in7", name: "OpenAI", category: "AI", connected: false, accounts: 0, description: "Use GPT models for drafts and summaries." },
  { id: "in8", name: "Webhooks", category: "Developer", connected: true, accounts: 4, description: "Forward events to any HTTPS endpoint." },
  { id: "in9", name: "REST API", category: "Developer", connected: true, accounts: 1, description: "Full programmatic access to JawCom." },
];

export const ASSISTANT_SUGGESTIONS = [
  { id: "as1", title: "Reply to Priya Sharma", body: "Absolutely — I have a 3:00 PM IST slot today. Should I send a calendar invite?", confidence: 92 },
  { id: "as2", title: "Reply to Daniel Chen", body: "Thanks Daniel — looping our procurement contact, Ana, into this thread.", confidence: 86 },
  { id: "as3", title: "Reply to Sofia Rossi", body: "Sharing the integration docs again — let me know if any sections feel unclear.", confidence: 81 },
];

export const ASSISTANT_INSIGHTS = [
  { id: "ai1", label: "High-intent leads today", value: "8", change: "+3 vs yesterday" },
  { id: "ai2", label: "Avg. response time", value: "4m 12s", change: "-38s this week" },
  { id: "ai3", label: "Sentiment score", value: "84%", change: "+6% this week" },
  { id: "ai4", label: "Stalled deals", value: "5", change: "Needs nudge" },
];

export const NEXT_BEST_ACTIONS = [
  { id: "nba1", text: "Send proposal to Priya Sharma — she's 92% likely to convert this week.", action: "Send" },
  { id: "nba2", text: "Reactivate Diego Alvarez — last engaged 14 days ago, opened recent campaign.", action: "Reactivate" },
  { id: "nba3", text: "Book demo with Hana Park — replied positively on pricing.", action: "Book" },
  { id: "nba4", text: "Loop AE on Daniel Chen — moving to procurement stage.", action: "Assign" },
];

export const TIMELINE = [
  { id: "tl1", time: "Today · 10:42 AM", type: "message", text: "Replied via WhatsApp: \"Yes, the proposal looks great…\"" },
  { id: "tl2", time: "Today · 9:14 AM", type: "email", text: "Opened email: \"Your Q1 proposal\"" },
  { id: "tl3", time: "Yesterday", type: "campaign", text: "Received Spring Promo 2026" },
  { id: "tl4", time: "Feb 10", type: "call", text: "Discovery call (28m) — notes added" },
  { id: "tl5", time: "Feb 8", type: "stage", text: "Stage moved: Qualified → Proposal" },
  { id: "tl6", time: "Feb 1", type: "note", text: "Maya added a note about budget constraints" },
];

export const API_KEYS = [
  { id: "ak1", name: "Production · Frontend", key: "jaw_live_p1k_••••••8Q4z", env: "Production", created: "Jan 14, 2026", lastUsed: "2m ago", scope: "read,write" },
  { id: "ak2", name: "Production · Backend", key: "jaw_live_b3v_••••••2X1m", env: "Production", created: "Dec 02, 2025", lastUsed: "14s ago", scope: "read,write,admin" },
  { id: "ak3", name: "Staging integration", key: "jaw_test_s9q_••••••L7tA", env: "Staging", created: "Feb 04, 2026", lastUsed: "1h ago", scope: "read,write" },
  { id: "ak4", name: "CI runner", key: "jaw_test_ci_••••••Hk3R", env: "Staging", created: "Feb 10, 2026", lastUsed: "3h ago", scope: "read" },
];

export const WEBHOOKS = [
  { id: "wh1", url: "https://api.acme.io/webhooks/jawcom", events: ["conversation.created", "message.received"], status: "Active", lastDelivery: "2m ago · 200 OK" },
  { id: "wh2", url: "https://hooks.zapier.com/hooks/catch/123/abc", events: ["lead.qualified"], status: "Active", lastDelivery: "14m ago · 200 OK" },
  { id: "wh3", url: "https://logs.internal.northwind.co/jawcom", events: ["campaign.sent", "campaign.completed"], status: "Paused", lastDelivery: "1d ago · 503" },
  { id: "wh4", url: "https://api.helio.com/webhooks/intent", events: ["ai.intent.detected"], status: "Active", lastDelivery: "8m ago · 200 OK" },
];

export const EVENT_LOGS = [
  { id: "ev1", time: "10:42:14", event: "conversation.created", payload: 'conv_id: "c_8X92n"', status: 200 },
  { id: "ev2", time: "10:42:13", event: "message.received", payload: 'msg_id: "m_24f7", channel: "whatsapp"', status: 200 },
  { id: "ev3", time: "10:41:58", event: "ai.intent.detected", payload: 'intent: "pricing", score: 0.92', status: 200 },
  { id: "ev4", time: "10:41:32", event: "campaign.sent", payload: 'campaign_id: "cp_spring26"', status: 200 },
  { id: "ev5", time: "10:40:11", event: "webhook.failed", payload: 'url: "https://logs.internal.northwind.co/jawcom"', status: 503 },
  { id: "ev6", time: "10:39:48", event: "lead.qualified", payload: 'customer_id: "cu_2"', status: 200 },
  { id: "ev7", time: "10:38:22", event: "workflow.executed", payload: 'wf_id: "wf_1", duration_ms: 1240', status: 200 },
  { id: "ev8", time: "10:38:01", event: "user.invited", payload: 'email: "kenji@jawcom.io"', status: 200 },
];

export const SDKS = [
  { id: "sdk1", lang: "JavaScript", pkg: "@jawcom/sdk", version: "1.4.2", install: "yarn add @jawcom/sdk" },
  { id: "sdk2", lang: "Python", pkg: "jawcom", version: "0.9.1", install: "pip install jawcom" },
  { id: "sdk3", lang: "Go", pkg: "github.com/jawcom/sdk-go", version: "0.3.0", install: "go get github.com/jawcom/sdk-go" },
  { id: "sdk4", lang: "Ruby", pkg: "jawcom-rb", version: "0.7.4", install: "gem install jawcom-rb" },
];

export const OAUTH_APPS = [
  { id: "oa1", name: "Acme Internal", clientId: "acme_int_42", scopes: "read:conversations write:messages", status: "Active" },
  { id: "oa2", name: "Helio Marketing", clientId: "helio_mkt_07", scopes: "read:campaigns", status: "Active" },
];

import PageHeader from "@/components/PageHeader";
import StatusBadge from "@/components/StatusBadge";
import DataTable from "@/components/DataTable";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { useState } from "react";
import {
  API_KEYS,
  WEBHOOKS,
  EVENT_LOGS,
  SDKS,
  OAUTH_APPS,
} from "@/dummy-data/developers";
import {
  Plus,
  Copy,
  Key,
  Webhook,
  Code,
  Cpu,
  Activity,
  ExternalLink,
  Lock,
  Play,
  FlaskConical,
  Shield,
  Gauge,
  Settings2,
  BookOpen,
  RefreshCw,
} from "lucide-react";

const WEBHOOK_LOGS = [
  { id: "wl1", time: "10:42:14", url: "api.acme.io/webhooks/jawcom", event: "conversation.created", status: 200, duration: "94 ms" },
  { id: "wl2", time: "10:41:58", url: "hooks.zapier.com/hooks/catch/123/abc", event: "lead.qualified", status: 200, duration: "212 ms" },
  { id: "wl3", time: "10:40:11", url: "logs.internal.northwind.co/jawcom", event: "campaign.sent", status: 503, duration: "3.4 s" },
  { id: "wl4", time: "10:38:22", url: "api.helio.com/webhooks/intent", event: "ai.intent.detected", status: 200, duration: "148 ms" },
  { id: "wl5", time: "10:33:04", url: "api.acme.io/webhooks/jawcom", event: "message.received", status: 200, duration: "72 ms" },
  { id: "wl6", time: "10:22:41", url: "hooks.zapier.com/hooks/catch/123/abc", event: "workflow.executed", status: 200, duration: "312 ms" },
];

const SECRETS = [
  { id: "s1", name: "ANTHROPIC_API_KEY", masked: "sk-ant-••••••Xa9Q", updated: "2 days ago", scope: "workspace" },
  { id: "s2", name: "OPENAI_API_KEY", masked: "sk-oa-••••••7ZmR", updated: "6 days ago", scope: "workspace" },
  { id: "s3", name: "WHATSAPP_TOKEN", masked: "EAAG••••••fLj2", updated: "Jan 22", scope: "workspace" },
  { id: "s4", name: "GMAIL_OAUTH", masked: "ya29.••••••kQ4v", updated: "Feb 3", scope: "workspace" },
  { id: "s5", name: "STRIPE_SECRET", masked: "sk_live_••••••42Zx", updated: "Feb 10", scope: "workspace" },
];

const RATE_LIMITS = [
  { name: "REST · read", limit: "1,000 req / min", used: 342, pct: 34 },
  { name: "REST · write", limit: "300 req / min", used: 128, pct: 42 },
  { name: "WhatsApp send", limit: "80 msg / sec", used: 44, pct: 55 },
  { name: "Email send", limit: "5,000 / hour", used: 3120, pct: 62 },
  { name: "Webhook out", limit: "500 / sec", used: 112, pct: 22 },
];

const DOC_LINKS = [
  { id: "d1", label: "REST API reference", desc: "Every endpoint, every parameter", href: "#" },
  { id: "d2", label: "Webhook event catalog", desc: "36 events, payload examples", href: "#" },
  { id: "d3", label: "SDK guides", desc: "JavaScript, Python, Go, Ruby", href: "#" },
  { id: "d4", label: "OAuth 2.0 flow", desc: "Authorize third-party apps", href: "#" },
  { id: "d5", label: "Best practices", desc: "Idempotency, retries, pagination", href: "#" },
  { id: "d6", label: "Changelog", desc: "API + SDK release notes", href: "#" },
];

export default function Developers() {
  const [testerUrl, setTesterUrl] = useState("https://api.acme.io/webhooks/jawcom");
  const [testerBody, setTesterBody] = useState('{\n  "event": "conversation.created",\n  "conv_id": "c_8X92n"\n}');

  return (
    <div data-testid="page-developers">
      <PageHeader
        title="Developer Hub"
        description="Keys, events, SDKs and everything you need to build on JawCom."
        actions={
          <Button variant="outline" size="sm" asChild data-testid="dev-open-docs">
            <a href="#" onClick={(e) => e.preventDefault()}>
              <ExternalLink className="mr-2 h-3.5 w-3.5" /> API docs
            </a>
          </Button>
        }
      />

      <div className="px-4 py-6 md:px-8">
        <Tabs defaultValue="keys" className="w-full">
          <TabsList className="mb-5 flex w-full justify-start overflow-x-auto scrollbar-thin">
            <TabsTrigger value="keys" className="text-xs" data-testid="dev-tab-keys"><Key className="mr-1.5 h-3.5 w-3.5" /> API Keys</TabsTrigger>
            <TabsTrigger value="webhooks" className="text-xs" data-testid="dev-tab-webhooks"><Webhook className="mr-1.5 h-3.5 w-3.5" /> Webhooks</TabsTrigger>
            <TabsTrigger value="wlogs" className="text-xs" data-testid="dev-tab-wlogs"><Activity className="mr-1.5 h-3.5 w-3.5" /> Webhook Logs</TabsTrigger>
            <TabsTrigger value="tester" className="text-xs" data-testid="dev-tab-tester"><FlaskConical className="mr-1.5 h-3.5 w-3.5" /> Webhook Tester</TabsTrigger>
            <TabsTrigger value="rest" className="text-xs" data-testid="dev-tab-rest"><Code className="mr-1.5 h-3.5 w-3.5" /> REST APIs</TabsTrigger>
            <TabsTrigger value="oauth" className="text-xs" data-testid="dev-tab-oauth"><Lock className="mr-1.5 h-3.5 w-3.5" /> OAuth</TabsTrigger>
            <TabsTrigger value="sandbox" className="text-xs" data-testid="dev-tab-sandbox"><Settings2 className="mr-1.5 h-3.5 w-3.5" /> Sandbox</TabsTrigger>
            <TabsTrigger value="events" className="text-xs" data-testid="dev-tab-events"><Activity className="mr-1.5 h-3.5 w-3.5" /> Event Logs</TabsTrigger>
            <TabsTrigger value="secrets" className="text-xs" data-testid="dev-tab-secrets"><Shield className="mr-1.5 h-3.5 w-3.5" /> Secrets</TabsTrigger>
            <TabsTrigger value="limits" className="text-xs" data-testid="dev-tab-limits"><Gauge className="mr-1.5 h-3.5 w-3.5" /> Rate Limits</TabsTrigger>
            <TabsTrigger value="env" className="text-xs" data-testid="dev-tab-env"><Cpu className="mr-1.5 h-3.5 w-3.5" /> Environment</TabsTrigger>
            <TabsTrigger value="docs" className="text-xs" data-testid="dev-tab-docs"><BookOpen className="mr-1.5 h-3.5 w-3.5" /> Docs</TabsTrigger>
          </TabsList>

          {/* API Keys */}
          <TabsContent value="keys">
            <Section title="API Keys" description="Long-lived keys for server-to-server access." action={<Button size="sm" data-testid="dev-generate-key"><Plus className="mr-2 h-3.5 w-3.5" /> Generate key</Button>}>
              <DataTable
                columns={[
                  { key: "name", label: "Name", render: (r) => <span className="text-sm font-semibold">{r.name}</span> },
                  { key: "key", label: "Key", render: (r) => <span className="font-mono text-xs">{r.key}</span> },
                  { key: "env", label: "Env", render: (r) => <StatusBadge status={r.env === "Production" ? "Active" : "Draft"} /> },
                  { key: "scope", label: "Scope", render: (r) => <span className="font-mono text-[11px] text-muted-foreground">{r.scope}</span> },
                  { key: "created", label: "Created", render: (r) => <span className="text-xs text-muted-foreground">{r.created}</span> },
                  { key: "lastUsed", label: "Last used", render: (r) => <span className="text-xs">{r.lastUsed}</span> },
                  { key: "actions", label: "", render: () => <Button variant="ghost" size="icon" className="h-7 w-7"><Copy className="h-3.5 w-3.5" /></Button> },
                ]}
                rows={API_KEYS}
                testId="api-keys-table"
              />
            </Section>
          </TabsContent>

          {/* Webhooks */}
          <TabsContent value="webhooks">
            <Section title="Webhooks" description="Endpoints receiving real-time events." action={<Button size="sm" data-testid="dev-add-webhook"><Plus className="mr-2 h-3.5 w-3.5" /> Add webhook</Button>}>
              <DataTable
                columns={[
                  { key: "url", label: "Endpoint", render: (r) => <span className="font-mono text-xs">{r.url}</span> },
                  { key: "events", label: "Events", render: (r) => (
                    <div className="flex flex-wrap gap-1">
                      {r.events.map((e) => <span key={e} className="rounded bg-secondary px-1.5 py-0.5 text-[10px] font-mono">{e}</span>)}
                    </div>
                  ) },
                  { key: "status", label: "Status", render: (r) => <StatusBadge status={r.status} /> },
                  { key: "lastDelivery", label: "Last delivery", render: (r) => <span className="text-xs text-muted-foreground">{r.lastDelivery}</span> },
                  { key: "actions", label: "", render: () => <Button variant="ghost" size="sm" className="h-7 text-xs">Configure</Button> },
                ]}
                rows={WEBHOOKS}
                testId="webhooks-table"
              />
            </Section>
          </TabsContent>

          {/* Webhook Logs */}
          <TabsContent value="wlogs">
            <Section title="Webhook logs" description="Live tail of outgoing webhook deliveries." action={<Button variant="outline" size="sm"><RefreshCw className="mr-2 h-3.5 w-3.5" /> Refresh</Button>}>
              <ul className="divide-y divide-border rounded-lg border border-border font-mono text-xs">
                {WEBHOOK_LOGS.map((l) => (
                  <li key={l.id} className="flex items-center gap-3 p-2.5">
                    <span className="w-20 shrink-0 text-muted-foreground">{l.time}</span>
                    <span className={`w-12 shrink-0 rounded px-1.5 py-0.5 text-center text-[10px] font-semibold ${l.status === 200 ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400" : "bg-rose-500/10 text-rose-600 dark:text-rose-400"}`}>{l.status}</span>
                    <span className="w-48 shrink-0 truncate font-semibold">{l.event}</span>
                    <span className="flex-1 truncate text-muted-foreground">{l.url}</span>
                    <span className="w-16 shrink-0 text-right text-muted-foreground">{l.duration}</span>
                  </li>
                ))}
              </ul>
            </Section>
          </TabsContent>

          {/* Webhook Tester */}
          <TabsContent value="tester">
            <Section title="Webhook tester" description="Fire a sample payload to any endpoint.">
              <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                <div className="space-y-3">
                  <div className="space-y-1.5">
                    <Label>Endpoint URL</Label>
                    <Input value={testerUrl} onChange={(e) => setTesterUrl(e.target.value)} data-testid="tester-url" />
                  </div>
                  <div className="space-y-1.5">
                    <Label>Event</Label>
                    <Select defaultValue="conversation.created">
                      <SelectTrigger data-testid="tester-event"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="conversation.created">conversation.created</SelectItem>
                        <SelectItem value="message.received">message.received</SelectItem>
                        <SelectItem value="lead.qualified">lead.qualified</SelectItem>
                        <SelectItem value="campaign.sent">campaign.sent</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1.5">
                    <Label>Payload</Label>
                    <Textarea rows={10} value={testerBody} onChange={(e) => setTesterBody(e.target.value)} className="font-mono text-xs" data-testid="tester-body" />
                  </div>
                  <Button size="sm" data-testid="tester-send"><Play className="mr-2 h-3.5 w-3.5" /> Send test</Button>
                </div>
                <Card className="rounded-xl border-border bg-card p-4">
                  <div className="mb-2 text-[10px] uppercase tracking-wider text-muted-foreground">Response</div>
                  <pre className="overflow-x-auto rounded-lg border border-border bg-secondary/40 p-3 font-mono text-xs leading-relaxed">{`HTTP/1.1 200 OK
X-Request-Id: req_8f2ab
Content-Type: application/json

{
  "ok": true,
  "received": ${new Date().getTime()}
}`}</pre>
                </Card>
              </div>
            </Section>
          </TabsContent>

          {/* REST */}
          <TabsContent value="rest">
            <Section title="REST APIs" description="Base URL and example requests.">
              <div className="space-y-3">
                <CodeBlock label="Base URL" code="https://api.jawcom.io/v1" />
                <CodeBlock label="cURL · List conversations" code={`curl -X GET https://api.jawcom.io/v1/conversations \\\n  -H "Authorization: Bearer jaw_live_..."`} />
                <CodeBlock label="cURL · Send message" code={`curl -X POST https://api.jawcom.io/v1/messages \\\n  -H "Authorization: Bearer jaw_live_..." \\\n  -H "Content-Type: application/json" \\\n  -d '{"to":"+91...","channel":"whatsapp","body":"Hi!"}'`} />
              </div>
            </Section>
          </TabsContent>

          {/* OAuth */}
          <TabsContent value="oauth">
            <Section title="OAuth apps" description="Third-party apps that act on behalf of users." action={<Button size="sm"><Plus className="mr-2 h-3.5 w-3.5" /> Create app</Button>}>
              <DataTable
                columns={[
                  { key: "name", label: "App", render: (r) => <span className="text-sm font-semibold">{r.name}</span> },
                  { key: "clientId", label: "Client ID", render: (r) => <span className="font-mono text-xs">{r.clientId}</span> },
                  { key: "scopes", label: "Scopes", render: (r) => <span className="font-mono text-[11px] text-muted-foreground">{r.scopes}</span> },
                  { key: "status", label: "Status", render: (r) => <StatusBadge status={r.status} /> },
                ]}
                rows={OAUTH_APPS}
                testId="oauth-table"
              />
            </Section>
          </TabsContent>

          {/* Sandbox */}
          <TabsContent value="sandbox">
            <Section title="Sandbox" description="Isolated environment for safe testing.">
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                <Card className="rounded-xl border-border bg-card p-4">
                  <div className="mb-2 flex items-center gap-2 text-sm font-bold"><FlaskConical className="h-4 w-4 text-primary" /> Sandbox workspace</div>
                  <p className="text-xs text-muted-foreground">Test messages, campaigns and journeys without touching production data. Reset any time.</p>
                  <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                    <Kv label="Base URL" value="sandbox.api.jawcom.io/v1" />
                    <Kv label="Env" value="staging" />
                    <Kv label="Test WhatsApp" value="+91 91 5555 0100" />
                    <Kv label="Reset window" value="Every 24h" />
                  </div>
                  <Button variant="outline" size="sm" className="mt-3 h-7 text-xs">Enter sandbox</Button>
                </Card>
                <Card className="rounded-xl border-border bg-card p-4">
                  <div className="mb-2 flex items-center gap-2 text-sm font-bold"><Cpu className="h-4 w-4 text-primary" /> SDKs</div>
                  <ul className="mt-2 space-y-2">
                    {SDKS.map((s) => (
                      <li key={s.id} className="rounded-md border border-border p-2 text-xs">
                        <div className="flex items-center justify-between">
                          <span className="font-semibold">{s.lang}</span>
                          <span className="font-mono text-[10px] text-muted-foreground">v{s.version}</span>
                        </div>
                        <div className="mt-1 font-mono text-[10px] text-muted-foreground">{s.install}</div>
                      </li>
                    ))}
                  </ul>
                </Card>
              </div>
            </Section>
          </TabsContent>

          {/* Event logs */}
          <TabsContent value="events">
            <Section title="Event logs" description="Live tail of API and system events." action={<Button variant="outline" size="sm">View all logs</Button>}>
              <ul className="divide-y divide-border rounded-lg border border-border font-mono text-xs">
                {EVENT_LOGS.map((e) => (
                  <li key={e.id} className="flex items-center gap-3 p-2.5">
                    <span className="w-20 shrink-0 text-muted-foreground">{e.time}</span>
                    <span className={`w-12 shrink-0 rounded px-1.5 py-0.5 text-center text-[10px] font-semibold ${e.status === 200 ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400" : "bg-rose-500/10 text-rose-600 dark:text-rose-400"}`}>{e.status}</span>
                    <span className="w-48 shrink-0 truncate font-semibold">{e.event}</span>
                    <span className="truncate text-muted-foreground">{e.payload}</span>
                  </li>
                ))}
              </ul>
            </Section>
          </TabsContent>

          {/* Secrets */}
          <TabsContent value="secrets">
            <Section title="Secrets" description="Sensitive values used by workflows and integrations." action={<Button size="sm"><Plus className="mr-2 h-3.5 w-3.5" /> Add secret</Button>}>
              <DataTable
                columns={[
                  { key: "name", label: "Name", render: (r) => <span className="font-mono text-sm font-semibold">{r.name}</span> },
                  { key: "masked", label: "Value", render: (r) => <span className="font-mono text-xs">{r.masked}</span> },
                  { key: "scope", label: "Scope", render: (r) => <span className="text-xs capitalize">{r.scope}</span> },
                  { key: "updated", label: "Last rotated", render: (r) => <span className="text-xs text-muted-foreground">{r.updated}</span> },
                  { key: "actions", label: "", render: () => <Button variant="ghost" size="sm" className="h-7 text-xs">Rotate</Button> },
                ]}
                rows={SECRETS}
                testId="secrets-table"
              />
            </Section>
          </TabsContent>

          {/* Rate Limits */}
          <TabsContent value="limits">
            <Section title="Rate limits" description="Live throughput vs your plan quotas.">
              <ul className="space-y-3">
                {RATE_LIMITS.map((r) => (
                  <li key={r.name} className="rounded-lg border border-border p-3">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-medium">{r.name}</span>
                      <span className="font-mono text-muted-foreground">{r.used.toLocaleString()} / {r.limit}</span>
                    </div>
                    <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-secondary">
                      <div className={`h-full rounded-full ${r.pct > 80 ? "bg-rose-500" : r.pct > 50 ? "bg-amber-500" : "bg-primary"}`} style={{ width: `${r.pct}%` }} />
                    </div>
                  </li>
                ))}
              </ul>
            </Section>
          </TabsContent>

          {/* Environment */}
          <TabsContent value="env">
            <Section title="Environment" description="Runtime and workspace configuration.">
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                <Card className="rounded-xl border-border bg-card p-4">
                  <div className="mb-2 text-sm font-bold">Runtime</div>
                  <ul className="space-y-1 text-xs">
                    <Kv label="Region" value="ap-south-1 · Mumbai" />
                    <Kv label="Cluster" value="prod-01" />
                    <Kv label="API version" value="v1.42.0" />
                    <Kv label="Uptime" value="99.98%" />
                  </ul>
                </Card>
                <Card className="rounded-xl border-border bg-card p-4">
                  <div className="mb-2 text-sm font-bold">Workspace</div>
                  <ul className="space-y-1 text-xs">
                    <Kv label="Workspace ID" value="ws_jaw_hq" />
                    <Kv label="Plan" value="Growth" />
                    <Kv label="Message quota" value="25,000 / mo" />
                    <Kv label="Data retention" value="365 days" />
                  </ul>
                </Card>
              </div>
            </Section>
          </TabsContent>

          {/* Documentation links */}
          <TabsContent value="docs">
            <Section title="Documentation" description="Everything you need to build with JawCom.">
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
                {DOC_LINKS.map((d) => (
                  <a
                    key={d.id}
                    href={d.href}
                    onClick={(e) => e.preventDefault()}
                    className="flex items-start gap-3 rounded-xl border border-border bg-card p-4 shadow-sm transition-colors hover:border-primary/30"
                    data-testid={`doc-link-${d.id}`}
                  >
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                      <BookOpen className="h-4 w-4" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-1 text-sm font-semibold">
                        {d.label} <ExternalLink className="h-3 w-3 text-muted-foreground" />
                      </div>
                      <div className="text-xs text-muted-foreground">{d.desc}</div>
                    </div>
                  </a>
                ))}
              </div>
            </Section>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

function Section({ title, description, action, children }) {
  return (
    <Card className="rounded-xl border-border bg-card p-5 shadow-sm">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-bold">{title}</h3>
          {description && <p className="mt-0.5 text-xs text-muted-foreground">{description}</p>}
        </div>
        {action}
      </div>
      {children}
    </Card>
  );
}

function CodeBlock({ label, code }) {
  return (
    <div>
      <div className="mb-1 flex items-center justify-between">
        <span className="text-[11px] uppercase tracking-wider text-muted-foreground">{label}</span>
        <Button variant="ghost" size="sm" className="h-6 text-[10px]">
          <Copy className="mr-1 h-3 w-3" /> Copy
        </Button>
      </div>
      <pre className="overflow-x-auto rounded-lg border border-border bg-secondary/40 p-3 font-mono text-xs leading-relaxed">{code}</pre>
    </div>
  );
}

function Kv({ label, value }) {
  return (
    <li className="flex items-center justify-between border-b border-border/60 py-1 text-xs last:border-b-0">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-mono font-medium">{value}</span>
    </li>
  );
}

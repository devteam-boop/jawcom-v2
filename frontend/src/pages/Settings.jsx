import PageHeader from "@/components/PageHeader";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import StatusBadge from "@/components/StatusBadge";

const TEAM = [
  { name: "Maya Iyer", email: "maya@jawcom.io", role: "Admin", initials: "MI" },
  { name: "Rohan Mehta", email: "rohan@jawcom.io", role: "Agent", initials: "RM" },
  { name: "Ana Souza", email: "ana@jawcom.io", role: "Manager", initials: "AS" },
  { name: "Kenji Watanabe", email: "kenji@jawcom.io", role: "Agent", initials: "KW" },
];

const ROLES = [
  { name: "Admin", description: "Full access including billing & users", members: 1 },
  { name: "Manager", description: "Manage campaigns, journeys & teams", members: 1 },
  { name: "Agent", description: "Reply to conversations & manage own pipeline", members: 2 },
  { name: "Viewer", description: "Read-only access to reports", members: 0 },
];

const TEMPLATES = [
  { name: "Welcome message", channel: "WhatsApp", language: "EN" },
  { name: "Pricing reminder", channel: "Email", language: "EN" },
  { name: "Demo confirmation", channel: "Email", language: "EN" },
  { name: "Renewal nudge", channel: "WhatsApp", language: "EN" },
];

export default function Settings() {
  return (
    <div data-testid="page-settings">
      <PageHeader title="Settings" description="Manage your workspace, team and preferences." />

      <div className="px-4 py-6 md:px-8">
        <Tabs defaultValue="workspace" className="w-full">
          <TabsList className="mb-6 flex w-full justify-start overflow-x-auto scrollbar-thin">
            <TabsTrigger value="workspace" data-testid="settings-tab-workspace">Workspace</TabsTrigger>
            <TabsTrigger value="users" data-testid="settings-tab-users">Users</TabsTrigger>
            <TabsTrigger value="roles" data-testid="settings-tab-roles">Roles</TabsTrigger>
            <TabsTrigger value="notifications" data-testid="settings-tab-notifications">Notifications</TabsTrigger>
            <TabsTrigger value="branding" data-testid="settings-tab-branding">Branding</TabsTrigger>
            <TabsTrigger value="templates" data-testid="settings-tab-templates">Templates</TabsTrigger>
            <TabsTrigger value="security" data-testid="settings-tab-security">Security</TabsTrigger>
          </TabsList>

          {/* Workspace */}
          <TabsContent value="workspace">
            <SettingCard title="Workspace details" description="General information about your workspace.">
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <Field label="Workspace name" defaultValue="JawCom HQ" />
                <Field label="Workspace URL" defaultValue="jawcom-hq.jawcom.io" />
                <Field label="Default language" defaultValue="English (India)" />
                <Field label="Time zone" defaultValue="Asia/Kolkata (IST)" />
              </div>
            </SettingCard>
            <SettingCard title="Billing" description="Plan and usage limits.">
              <div className="flex items-center justify-between rounded-lg border border-border p-4">
                <div>
                  <div className="text-sm font-semibold">Growth Plan</div>
                  <div className="text-xs text-muted-foreground">25,000 messages / month · 8 seats</div>
                </div>
                <Button variant="outline" size="sm">Manage plan</Button>
              </div>
            </SettingCard>
          </TabsContent>

          {/* Users */}
          <TabsContent value="users">
            <SettingCard title="Team members" description="Add and manage who has access." action={<Button size="sm">Invite user</Button>}>
              <ul className="divide-y divide-border">
                {TEAM.map((u) => (
                  <li key={u.email} className="flex items-center gap-3 py-3">
                    <Avatar className="h-9 w-9">
                      <AvatarFallback className="bg-primary/10 text-[11px] font-semibold text-primary">
                        {u.initials}
                      </AvatarFallback>
                    </Avatar>
                    <div className="min-w-0 flex-1">
                      <div className="text-sm font-semibold">{u.name}</div>
                      <div className="text-xs text-muted-foreground">{u.email}</div>
                    </div>
                    <StatusBadge status={u.role === "Admin" ? "Active" : "Assigned"} />
                    <Button variant="ghost" size="sm" className="text-xs">Manage</Button>
                  </li>
                ))}
              </ul>
            </SettingCard>
          </TabsContent>

          {/* Roles */}
          <TabsContent value="roles">
            <SettingCard title="Roles & permissions" description="Define what each role can do." action={<Button size="sm" variant="outline">New role</Button>}>
              <ul className="divide-y divide-border">
                {ROLES.map((r) => (
                  <li key={r.name} className="flex items-center justify-between py-3">
                    <div>
                      <div className="text-sm font-semibold">{r.name}</div>
                      <div className="text-xs text-muted-foreground">{r.description}</div>
                    </div>
                    <div className="text-xs text-muted-foreground">{r.members} members</div>
                  </li>
                ))}
              </ul>
            </SettingCard>
          </TabsContent>

          {/* Notifications */}
          <TabsContent value="notifications">
            <SettingCard title="Notification preferences" description="Control when and how you're notified.">
              <div className="space-y-3">
                <NotifRow label="New conversations" description="Get notified when a customer messages you." defaultChecked />
                <NotifRow label="Mentions" description="When a teammate @-mentions you in a thread." defaultChecked />
                <NotifRow label="AI suggestions" description="When the assistant drafts a high-confidence reply." />
                <NotifRow label="Campaign performance" description="Daily summary of running campaigns." defaultChecked />
                <NotifRow label="Daily digest" description="Morning digest of the day ahead." />
              </div>
            </SettingCard>
          </TabsContent>

          {/* Branding */}
          <TabsContent value="branding">
            <SettingCard title="Branding" description="How JawCom looks to your customers.">
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <Field label="Brand name" defaultValue="JawCom" />
                <Field label="Reply-to email" defaultValue="hello@jawcom.io" />
                <Field label="Brand color" defaultValue="#4F46E5" />
                <Field label="Signature" defaultValue="– Maya, JawCom" />
              </div>
              <div className="mt-4 rounded-lg border border-dashed border-border p-6 text-center text-sm text-muted-foreground">
                Drop your logo here, or <span className="font-medium text-primary">browse</span>
              </div>
            </SettingCard>
          </TabsContent>

          {/* Templates */}
          <TabsContent value="templates">
            <SettingCard title="Message templates" description="Approved templates for outbound messaging." action={<Button size="sm">New template</Button>}>
              <ul className="divide-y divide-border">
                {TEMPLATES.map((t) => (
                  <li key={t.name} className="flex items-center justify-between py-3">
                    <div>
                      <div className="text-sm font-semibold">{t.name}</div>
                      <div className="text-xs text-muted-foreground">{t.channel} · {t.language}</div>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <StatusBadge status="Active" />
                      <Button variant="ghost" size="sm" className="text-xs">Edit</Button>
                    </div>
                  </li>
                ))}
              </ul>
            </SettingCard>
          </TabsContent>

          {/* Security */}
          <TabsContent value="security">
            <SettingCard title="Security" description="Protect your workspace.">
              <div className="space-y-3">
                <NotifRow label="Two-factor authentication" description="Require 2FA for all team members." defaultChecked />
                <NotifRow label="Session timeout" description="Auto sign-out after 30 minutes of inactivity." />
                <NotifRow label="IP allowlist" description="Restrict logins to known IPs." />
                <NotifRow label="SSO (SAML)" description="Sign in with your identity provider." />
              </div>
              <Separator className="my-5" />
              <div>
                <Label>Audit log</Label>
                <Textarea
                  rows={4}
                  defaultValue={"Feb 14, 10:42 — Maya signed in from Mumbai\nFeb 14, 09:01 — Rohan created campaign 'Demo Day Invite'\nFeb 13, 18:22 — Ana invited kenji@jawcom.io"}
                  readOnly
                  className="mt-1.5 font-mono text-xs"
                />
              </div>
            </SettingCard>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

function SettingCard({ title, description, action, children }) {
  return (
    <Card className="mb-4 rounded-xl border-border bg-card p-6 shadow-sm">
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

function Field({ label, defaultValue }) {
  return (
    <div className="space-y-1.5">
      <Label>{label}</Label>
      <Input defaultValue={defaultValue} />
    </div>
  );
}

function NotifRow({ label, description, defaultChecked }) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-border p-3">
      <div>
        <div className="text-sm font-medium">{label}</div>
        <div className="text-xs text-muted-foreground">{description}</div>
      </div>
      <Switch defaultChecked={defaultChecked} />
    </div>
  );
}

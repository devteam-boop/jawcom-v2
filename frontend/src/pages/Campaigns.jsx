import { useMemo, useState } from "react";
import PageHeader from "@/components/PageHeader";
import FilterBar from "@/components/FilterBar";
import StatusBadge from "@/components/StatusBadge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import { CAMPAIGNS } from "@/dummy-data";
import { TEMPLATES } from "@/dummy-data/templates";
import {
  Plus,
  Users,
  Send,
  Eye,
  Reply,
  Calendar,
  CheckCircle2,
  Copy,
  Pause,
  BarChart3,
  FileText,
  Rocket,
  ChevronRight,
  ChevronLeft,
  Sparkles,
} from "lucide-react";

// ---- Approval + delivered/read enrichment ----
const APPROVAL_CYCLE = ["Approved", "Approved", "Approved", "Pending", "Approved", "Approved", "Pending", "Rejected"];

function enrichCampaign(c, i) {
  const templates = [
    ...TEMPLATES.whatsapp.map((t) => ({ ...t, channel: "WhatsApp" })),
    ...TEMPLATES.email.map((t) => ({ ...t, channel: "Email" })),
    ...TEMPLATES.sms.map((t) => ({ ...t, channel: "SMS" })),
  ];
  const template = templates[i % templates.length];
  const delivered = Math.round(c.sent * 0.96);
  const read = Math.round(c.opens * 0.98);
  const approval = APPROVAL_CYCLE[i % APPROVAL_CYCLE.length];
  return { ...c, template, delivered, read, approval };
}

const approvalTone = {
  Approved: "border-emerald-500/20 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400",
  Pending: "border-amber-500/20 bg-amber-500/10 text-amber-700 dark:text-amber-400",
  Rejected: "border-rose-500/20 bg-rose-500/10 text-rose-700 dark:text-rose-400",
};

const FILTERS = [
  { label: "All", value: "all" },
  { label: "Draft", value: "Draft" },
  { label: "Scheduled", value: "Scheduled" },
  { label: "Running", value: "Running" },
  { label: "Completed", value: "Completed" },
];

const channelColor = {
  WhatsApp: "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400",
  Email: "bg-blue-500/10 text-blue-700 dark:text-blue-400",
  SMS: "bg-amber-500/10 text-amber-700 dark:text-amber-400",
  Instagram: "bg-pink-500/10 text-pink-700 dark:text-pink-400",
};

const APPROVED_TEMPLATES = [
  ...TEMPLATES.whatsapp.filter((t) => t.status === "Approved").map((t) => ({ ...t, channel: "WhatsApp" })),
  ...TEMPLATES.email.filter((t) => t.status === "Approved").map((t) => ({ ...t, channel: "Email" })),
  ...TEMPLATES.sms.filter((t) => t.status === "Approved").map((t) => ({ ...t, channel: "SMS" })),
];

export default function Campaigns() {
  const [filter, setFilter] = useState("all");
  const [wizardOpen, setWizardOpen] = useState(false);

  const rows = useMemo(
    () =>
      CAMPAIGNS.map(enrichCampaign).filter((c) => filter === "all" || c.status === filter),
    [filter]
  );

  const filterOptions = FILTERS.map((f) => ({
    ...f,
    count: f.value === "all" ? CAMPAIGNS.length : CAMPAIGNS.filter((c) => c.status === f.value).length,
  }));

  return (
    <div data-testid="page-campaigns">
      <PageHeader
        title="Campaigns"
        description="Broadcast approved templates to your audiences."
        actions={
          <Button size="sm" onClick={() => setWizardOpen(true)} data-testid="campaign-new">
            <Plus className="mr-2 h-3.5 w-3.5" /> New campaign
          </Button>
        }
      />

      {/* Product flow strip */}
      <div className="mx-4 mt-6 flex flex-wrap items-center gap-1 rounded-xl border border-border bg-card p-2.5 text-xs md:mx-8" data-testid="campaign-flow">
        {["Template", "Approval", "Campaign", "Broadcast", "Analytics"].map((step, i, arr) => (
          <span key={step} className="flex items-center gap-1">
            <span className={cn(
              "rounded-md px-2 py-1 font-medium",
              i === 2 ? "bg-primary/10 text-primary" : "bg-secondary text-muted-foreground"
            )}>
              {step}
            </span>
            {i < arr.length - 1 && <ChevronRight className="h-3 w-3 text-muted-foreground" />}
          </span>
        ))}
      </div>

      <div className="space-y-5 px-4 py-6 md:px-8">
        <FilterBar options={filterOptions} value={filter} onChange={setFilter} testId="campaigns-filter" />

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {rows.map((c) => (
            <Card
              key={c.id}
              className="rounded-xl border-border bg-card p-5 shadow-sm transition-colors hover:border-primary/30"
              data-testid={`campaign-${c.id}`}
            >
              {/* Header */}
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className={cn("inline-flex rounded-md px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider", channelColor[c.channel] || "bg-secondary")}>
                      {c.channel}
                    </span>
                    <ApprovalBadge status={c.approval} />
                  </div>
                  <h3 className="mt-2 truncate text-base font-bold">{c.name}</h3>
                  <p className="mt-0.5 flex items-center gap-1 truncate text-xs text-muted-foreground">
                    <FileText className="h-3 w-3" /> Template · {c.template?.name || "—"}
                  </p>
                </div>
                <StatusBadge status={c.status} />
              </div>

              {/* Audience + Schedule */}
              <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
                <div className="rounded-lg border border-border p-2.5">
                  <div className="flex items-center gap-1 text-[10px] uppercase tracking-wider text-muted-foreground">
                    <Users className="h-3 w-3" /> Audience
                  </div>
                  <div className="mt-0.5 font-mono text-sm font-semibold">{c.audience.toLocaleString()}</div>
                </div>
                <div className="rounded-lg border border-border p-2.5">
                  <div className="flex items-center gap-1 text-[10px] uppercase tracking-wider text-muted-foreground">
                    <Calendar className="h-3 w-3" /> Schedule
                  </div>
                  <div className="mt-0.5 truncate text-xs font-medium">{c.schedule}</div>
                </div>
              </div>

              {/* Broadcast metrics */}
              <div className="mt-4 grid grid-cols-4 gap-2 border-t border-border pt-4">
                <Metric icon={Send} label="Sent" value={c.sent.toLocaleString()} />
                <Metric icon={CheckCircle2} label="Delivered" value={c.delivered.toLocaleString()} />
                <Metric icon={Eye} label="Read" value={c.read.toLocaleString()} />
                <Metric icon={Reply} label="Replies" value={c.replies.toLocaleString()} />
              </div>

              {/* Actions */}
              <div className="mt-4 grid grid-cols-4 gap-1.5">
                <Button variant="outline" size="sm" className="h-7 text-[11px]" data-testid={`campaign-preview-${c.id}`}>
                  <Eye className="mr-1 h-3 w-3" /> Preview
                </Button>
                <Button variant="outline" size="sm" className="h-7 text-[11px]" data-testid={`campaign-duplicate-${c.id}`}>
                  <Copy className="mr-1 h-3 w-3" /> Dup
                </Button>
                <Button variant="outline" size="sm" className="h-7 text-[11px]" data-testid={`campaign-pause-${c.id}`}>
                  <Pause className="mr-1 h-3 w-3" /> Pause
                </Button>
                <Button variant="outline" size="sm" className="h-7 text-[11px]" data-testid={`campaign-analytics-${c.id}`}>
                  <BarChart3 className="mr-1 h-3 w-3" /> Stats
                </Button>
              </div>
            </Card>
          ))}
        </div>
      </div>

      <CampaignWizard open={wizardOpen} onOpenChange={setWizardOpen} />
    </div>
  );
}

function ApprovalBadge({ status }) {
  return (
    <Badge
      variant="outline"
      className={cn("h-4 px-1.5 text-[10px] font-semibold", approvalTone[status])}
      data-testid={`approval-${status}`}
    >
      {status}
    </Badge>
  );
}

function Metric({ icon: Icon, label, value }) {
  return (
    <div>
      <div className="flex items-center gap-1 text-[10px] uppercase tracking-wider text-muted-foreground">
        <Icon className="h-3 w-3" /> {label}
      </div>
      <div className="mt-0.5 font-mono text-sm font-semibold">{value}</div>
    </div>
  );
}

// -------------------- 5-step wizard --------------------
const STEPS = [
  { id: 1, key: "template", label: "Select Template" },
  { id: 2, key: "audience", label: "Audience" },
  { id: 3, key: "schedule", label: "Schedule" },
  { id: 4, key: "review", label: "Review" },
  { id: 5, key: "launch", label: "Launch" },
];

function CampaignWizard({ open, onOpenChange }) {
  const [step, setStep] = useState(1);
  const [templateId, setTemplateId] = useState(APPROVED_TEMPLATES[0]?.id || "");
  const [audience, setAudience] = useState("all");
  const [scheduleType, setScheduleType] = useState("now");
  const [scheduleDate, setScheduleDate] = useState("2026-02-20T10:00");
  const [name, setName] = useState("Q2 Renewal Push");

  const template = APPROVED_TEMPLATES.find((t) => t.id === templateId);

  const canNext =
    (step === 1 && !!templateId) ||
    (step === 2 && !!audience) ||
    (step === 3 && (scheduleType === "now" || scheduleDate)) ||
    step === 4 ||
    step === 5;

  const reset = () => {
    setStep(1);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) reset(); else onOpenChange(true); }}>
      <DialogContent className="sm:max-w-2xl" data-testid="campaign-wizard">
        <DialogHeader>
          <DialogTitle>New campaign</DialogTitle>
          <DialogDescription>Broadcast an approved template to a chosen audience.</DialogDescription>
        </DialogHeader>

        {/* Stepper */}
        <div className="flex items-center gap-1.5 border-b border-border pb-3">
          {STEPS.map((s, i) => {
            const active = s.id === step;
            const done = s.id < step;
            return (
              <div key={s.id} className="flex flex-1 items-center gap-1.5">
                <div
                  className={cn(
                    "flex h-6 w-6 items-center justify-center rounded-full border text-[10px] font-bold",
                    active
                      ? "border-primary bg-primary text-primary-foreground"
                      : done
                      ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                      : "border-border bg-secondary text-muted-foreground"
                  )}
                  data-testid={`wizard-step-${s.id}`}
                >
                  {done ? <CheckCircle2 className="h-3 w-3" /> : s.id}
                </div>
                <span className={cn("text-[11px]", active ? "font-semibold" : "text-muted-foreground")}>{s.label}</span>
                {i < STEPS.length - 1 && <span className="ml-1 h-px flex-1 bg-border" />}
              </div>
            );
          })}
        </div>

        {/* Step content */}
        <div className="min-h-[280px] py-1">
          {step === 1 && (
            <div className="space-y-3" data-testid="wizard-step-template">
              <p className="text-xs text-muted-foreground">Only templates with <span className="font-semibold text-emerald-600 dark:text-emerald-400">Approved</span> status can be launched.</p>
              <div className="max-h-64 space-y-1.5 overflow-y-auto scrollbar-thin">
                {APPROVED_TEMPLATES.map((t) => {
                  const active = t.id === templateId;
                  return (
                    <button
                      key={t.id}
                      onClick={() => setTemplateId(t.id)}
                      className={cn(
                        "flex w-full items-start gap-3 rounded-lg border p-3 text-left transition-colors",
                        active ? "border-primary bg-primary/5" : "border-border bg-card hover:border-primary/30"
                      )}
                      data-testid={`wizard-template-${t.id}`}
                    >
                      <span className={cn("inline-flex rounded-md px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider", channelColor[t.channel] || "bg-secondary")}>
                        {t.channel}
                      </span>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-1.5">
                          <span className="truncate text-sm font-semibold">{t.name}</span>
                          <ApprovalBadge status="Approved" />
                        </div>
                        <p className="mt-0.5 line-clamp-1 text-xs text-muted-foreground">{t.preview.split("\n")[0]}</p>
                      </div>
                      {active && <CheckCircle2 className="mt-0.5 h-4 w-4 text-primary" />}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4" data-testid="wizard-step-audience">
              <div className="space-y-1.5">
                <Label>Audience segment</Label>
                <Select value={audience} onValueChange={setAudience}>
                  <SelectTrigger data-testid="wizard-audience"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All contacts</SelectItem>
                    <SelectItem value="leads">Leads only</SelectItem>
                    <SelectItem value="active">Active customers</SelectItem>
                    <SelectItem value="renewals">Renewals due (30d)</SelectItem>
                    <SelectItem value="vip">VIP list</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="rounded-lg border border-border bg-card p-3 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Estimated audience size</span>
                  <span className="font-mono text-sm font-semibold">
                    {audience === "vip" ? "64" : audience === "renewals" ? "184" : audience === "leads" ? "1,240" : audience === "active" ? "3,420" : "12,480"}
                  </span>
                </div>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-4" data-testid="wizard-step-schedule">
              <div className="space-y-1.5">
                <Label>When to send</Label>
                <Select value={scheduleType} onValueChange={setScheduleType}>
                  <SelectTrigger data-testid="wizard-schedule-type"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="now">Send immediately</SelectItem>
                    <SelectItem value="later">Schedule for later</SelectItem>
                    <SelectItem value="recurring">Recurring</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              {scheduleType === "later" && (
                <div className="space-y-1.5">
                  <Label>Date & time</Label>
                  <Input
                    type="datetime-local"
                    value={scheduleDate}
                    onChange={(e) => setScheduleDate(e.target.value)}
                    data-testid="wizard-schedule-date"
                  />
                </div>
              )}
              <div className="space-y-1.5">
                <Label>Campaign name</Label>
                <Input value={name} onChange={(e) => setName(e.target.value)} data-testid="wizard-name" />
              </div>
            </div>
          )}

          {step === 4 && (
            <div className="space-y-3" data-testid="wizard-step-review">
              <ReviewRow label="Campaign name" value={name} />
              <ReviewRow label="Template" value={template?.name || "—"} />
              <ReviewRow label="Channel" value={template?.channel || "—"} />
              <ReviewRow label="Approval" value={<ApprovalBadge status="Approved" />} />
              <ReviewRow label="Audience" value={audience} />
              <ReviewRow label="Schedule" value={scheduleType === "now" ? "Send immediately" : scheduleType === "recurring" ? "Recurring" : scheduleDate.replace("T", " · ")} />
            </div>
          )}

          {step === 5 && (
            <div className="flex flex-col items-center justify-center gap-3 py-8" data-testid="wizard-step-launch">
              <div className="flex h-14 w-14 items-center justify-center rounded-full bg-primary/10 text-primary">
                <Rocket className="h-6 w-6" />
              </div>
              <h3 className="text-lg font-bold">Ready to launch</h3>
              <p className="max-w-sm text-center text-sm text-muted-foreground">
                “{name}” will broadcast to your selected audience using the approved template.
              </p>
              <div className="flex items-center gap-1.5 rounded-full bg-secondary px-3 py-1 text-xs">
                <Sparkles className="h-3 w-3 text-primary" />
                <span>AI will monitor delivery & sentiment in real time.</span>
              </div>
            </div>
          )}
        </div>

        <DialogFooter className="flex-row items-center justify-between border-t border-border pt-3 sm:justify-between">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setStep((s) => Math.max(1, s - 1))}
            disabled={step === 1}
            data-testid="wizard-back"
          >
            <ChevronLeft className="mr-1 h-3.5 w-3.5" /> Back
          </Button>
          {step < 5 ? (
            <Button size="sm" onClick={() => setStep((s) => s + 1)} disabled={!canNext} data-testid="wizard-next">
              Next <ChevronRight className="ml-1 h-3.5 w-3.5" />
            </Button>
          ) : (
            <Button size="sm" onClick={reset} data-testid="wizard-launch">
              <Rocket className="mr-2 h-3.5 w-3.5" /> Launch campaign
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function ReviewRow({ label, value }) {
  return (
    <div className="flex items-center justify-between border-b border-border/60 pb-2">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className="text-sm font-medium">{value}</span>
    </div>
  );
}

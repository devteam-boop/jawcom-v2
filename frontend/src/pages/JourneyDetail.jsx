import { useParams, Navigate, useLocation, useNavigate } from "react-router-dom";
import { useState, useEffect, useCallback } from "react";
import { cn } from "@/lib/utils";
import PageHeader from "@/components/PageHeader";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  JourneyDashboard,
  RunningInstances,
  JourneySettings,
  FlowBuilder,
  TriggerConfiguration,
  TestJourneyDialog,
} from "@/modules/journeys";
import { useJourney } from "@/modules/journeys";
import { stageMappingService } from "@/services/stageMappings";
import { runningInstanceService } from "@/services/runningInstances";
import { journeyService } from "@/services/journeys";
import { toast } from "sonner";
import {
  CheckCircle2,
  Circle,
  ChevronRight,
  Loader2,
  Play,
  ArrowLeft,
  UploadCloud,
} from "lucide-react";

const SECTIONS = [
  { key: "dashboard", label: "Dashboard" },
  { key: "flow", label: "Flow" },
  { key: "running", label: "Running" },
  { key: "settings", label: "Settings" },
];

const WIZARD_STEPS = [
  { key: "details", label: "Journey Details" },
  { key: "trigger", label: "Trigger Stage" },
  { key: "flow", label: "Flow Builder" },
  { key: "publish", label: "Publish" },
];

export default function JourneyDetail() {
  const { id } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const section = location.pathname.split("/").pop() || "dashboard";
  const { journey, loading, refetch } = useJourney(id);
  const [mappings, setMappings] = useState([]);
  const [instances, setInstances] = useState([]);
  const [actionLoading, setActionLoading] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [testOpen, setTestOpen] = useState(false);

  const [wizardStep, setWizardStep] = useState("details");
  const [editName, setEditName] = useState("");
  const [editDesc, setEditDesc] = useState("");
  const [publishResult, setPublishResult] = useState(null);
  const [publishing, setPublishing] = useState(false);

  const fetchInstances = useCallback(() => {
    if (!id) return;
    runningInstanceService.list({ journeyId: id }).then(setInstances).catch(() => {});
  }, [id]);

  useEffect(() => {
    if (!id) return;
    stageMappingService.list({ journeyId: id }).then(setMappings).catch(() => {});
    fetchInstances();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  useEffect(() => {
    if (journey) {
      setEditName(journey.name || "");
      setEditDesc(journey.description || "");
    }
  }, [journey]);

  const handleTabChange = (value) => {
    navigate(`/journeys/${id}/${value}`);
  };

  const handleAction = async (action) => {
    setActionLoading(true);
    try {
      if (action === "activate") await journeyService.activate(id);
      else if (action === "pause") await journeyService.pause(id);
      else if (action === "archive") await journeyService.archive(id);
      refetch();
    } catch (err) {
      console.error(`${action} failed`, err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleDelete = async () => {
    setActionLoading(true);
    try {
      await journeyService.delete(id);
      setDeleteOpen(false);
      navigate("/journeys", { replace: true });
    } catch (err) {
      console.error("Delete failed", err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleSaveDetails = async () => {
    if (!editName.trim()) {
      toast.error("Journey name is required");
      return;
    }
    try {
      await journeyService.update(id, { name: editName.trim(), description: editDesc.trim() || null });
      refetch();
      toast.success("Journey details updated");
    } catch (err) {
      toast.error(err?.message || "Failed to update journey");
    }
  };

  const handlePublish = async () => {
    setPublishing(true);
    setPublishResult(null);
    try {
      const res = await journeyService.publish(id);
      setPublishResult(res);
      if (res.success) {
        toast.success("Journey published and activated");
        refetch();
      }
    } catch (err) {
      const msg = err?.message || "Publish failed";
      setPublishResult({ success: false, message: msg, errors: [msg] });
      toast.error(msg);
    } finally {
      setPublishing(false);
    }
  };

  const triggerMapping = mappings.length > 0 ? mappings[0] : null;
  const hasFlow = !!journey?.flow_definition_id;

  const stepStatus = {
    details: journey?.name ? "done" : "pending",
    trigger: triggerMapping ? "done" : "pending",
    flow: hasFlow ? "done" : "pending",
    publish: "pending",
  };

  if (loading) {
    return (
      <div data-testid="page-journey-detail" className="flex h-full min-h-0 flex-col items-center justify-center text-sm text-muted-foreground">
        Loading journey…
      </div>
    );
  }

  if (!journey) {
    return <Navigate to="/journeys" replace />;
  }

  const isDraft = journey.status === "draft";

  const renderWizard = () => (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex items-center gap-2 border-b border-border bg-card px-6 py-3">
        {WIZARD_STEPS.map((step, i) => {
          const active = step.key === wizardStep;
          const status = stepStatus[step.key];
          const done = status === "done";
          const isLast = i === WIZARD_STEPS.length - 1;
          return (
            <div key={step.key} className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setWizardStep(step.key)}
                className={cn(
                  "flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium transition-colors",
                  active
                    ? "bg-primary/10 text-primary"
                    : done
                      ? "text-emerald-600 hover:bg-emerald-500/10"
                      : "text-muted-foreground hover:bg-secondary"
                )}
              >
                {done ? (
                  <CheckCircle2 className="h-3.5 w-3.5" />
                ) : (
                  <Circle className="h-3.5 w-3.5" />
                )}
                {step.label}
              </button>
              {!isLast && <Separator className="w-6" />}
            </div>
          );
        })}
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-thin">
        {wizardStep === "details" && (
          <div className="mx-auto max-w-2xl space-y-6 p-6">
            <div>
              <h3 className="text-lg font-bold">Journey Details</h3>
              <p className="text-sm text-muted-foreground">Configure the basic information for this journey.</p>
            </div>

            <Card className="rounded-xl border-border bg-card p-5">
              <div className="space-y-4">
                <div className="space-y-1.5">
                  <Label htmlFor="wiz-name">Name</Label>
                  <Input
                    id="wiz-name"
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    placeholder="e.g. Lead Qualification"
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="wiz-desc">Description</Label>
                  <Input
                    id="wiz-desc"
                    value={editDesc}
                    onChange={(e) => setEditDesc(e.target.value)}
                    placeholder="Optional description"
                  />
                </div>
                <Button size="sm" onClick={handleSaveDetails}>
                  Save Details
                </Button>
              </div>
            </Card>

            <div className="flex justify-end">
              <Button onClick={() => setWizardStep("trigger")}>
                Next: Trigger Stage <ChevronRight className="ml-1 h-4 w-4" />
              </Button>
            </div>
          </div>
        )}

        {wizardStep === "trigger" && (
          <div className="mx-auto max-w-2xl space-y-6 p-6">
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm" onClick={() => setWizardStep("details")}>
                <ArrowLeft className="mr-1 h-3.5 w-3.5" /> Back
              </Button>
            </div>

            <TriggerConfiguration
              journeyId={id}
              mappings={mappings}
              onRefresh={() => {
                stageMappingService.list({ journeyId: id }).then(setMappings).catch(() => {});
              }}
            />

            <div className="flex justify-end">
              <Button
                onClick={() => setWizardStep("flow")}
                disabled={!triggerMapping}
                title={!triggerMapping ? "Configure a trigger stage first" : ""}
              >
                Next: Flow Builder <ChevronRight className="ml-1 h-4 w-4" />
              </Button>
            </div>
          </div>
        )}

        {wizardStep === "flow" && (
          <div className="flex h-full min-h-0 flex-col">
            <div className="flex items-center gap-2 border-b border-border bg-background px-6 py-2">
              <Button variant="ghost" size="sm" onClick={() => setWizardStep("trigger")}>
                <ArrowLeft className="mr-1 h-3.5 w-3.5" /> Back
              </Button>
              <span className="text-xs text-muted-foreground">Build your flow, then save and publish it.</span>
            </div>
            <div className="flex-1 min-h-0">
              <FlowBuilder journeyId={id} journeyName={journey.name} />
            </div>
            <div className="flex justify-end border-t border-border bg-background px-6 py-3">
              <Button onClick={() => setWizardStep("publish")}>
                Next: Publish <ChevronRight className="ml-1 h-4 w-4" />
              </Button>
            </div>
          </div>
        )}

        {wizardStep === "publish" && (
          <div className="mx-auto max-w-2xl space-y-6 p-6">
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm" onClick={() => setWizardStep("flow")}>
                <ArrowLeft className="mr-1 h-3.5 w-3.5" /> Back
              </Button>
            </div>

            <div>
              <h3 className="text-lg font-bold">Publish Journey</h3>
              <p className="text-sm text-muted-foreground">
                Review the checklist below before publishing. Once published, the journey will be active and ready for leads.
              </p>
            </div>

            <Card className="rounded-xl border-border bg-card p-5">
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  {stepStatus.details === "done" ? (
                    <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                  ) : (
                    <Circle className="h-5 w-5 text-muted-foreground" />
                  )}
                  <div>
                    <div className="text-sm font-medium">Journey Details</div>
                    <div className="text-xs text-muted-foreground">{journey.name}</div>
                  </div>
                </div>

                <Separator />

                <div className="flex items-center gap-3">
                  {stepStatus.trigger === "done" ? (
                    <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                  ) : (
                    <Circle className="h-5 w-5 text-muted-foreground" />
                  )}
                  <div>
                    <div className="text-sm font-medium">Trigger Stage</div>
                    <div className="text-xs text-muted-foreground">
                      {triggerMapping?.stage_key || "Not configured"}
                    </div>
                  </div>
                </div>

                <Separator />

                <div className="flex items-center gap-3">
                  {hasFlow ? (
                    <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                  ) : (
                    <Circle className="h-5 w-5 text-muted-foreground" />
                  )}
                  <div>
                    <div className="text-sm font-medium">Flow Definition</div>
                    <div className="text-xs text-muted-foreground">
                      {hasFlow ? "Flow created" : "No flow created"}
                    </div>
                  </div>
                </div>
              </div>
            </Card>

            {publishResult && !publishResult.success && (
              <Card className="rounded-xl border-red-500/30 bg-red-500/5 p-4">
                <div className="text-sm font-semibold text-red-700">{publishResult.message}</div>
                {publishResult.errors?.length > 0 && (
                  <ul className="mt-2 list-inside list-disc space-y-1 text-xs text-red-600">
                    {publishResult.errors.map((err, i) => (
                      <li key={i}>{err}</li>
                    ))}
                  </ul>
                )}
              </Card>
            )}

            {publishResult && publishResult.success && (
              <Card className="rounded-xl border-emerald-500/30 bg-emerald-500/5 p-4">
                <div className="flex items-center gap-2 text-sm font-semibold text-emerald-700">
                  <CheckCircle2 className="h-4 w-4" />
                  {publishResult.message}
                </div>
              </Card>
            )}

            <div className="flex justify-end">
              <Button size="lg" onClick={handlePublish} disabled={publishing || publishResult?.success}>
                {publishing ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <UploadCloud className="mr-2 h-4 w-4" />
                )}
                {publishResult?.success ? "Published" : "Publish Journey"}
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );

  const renderTabs = () => (
    <>
      <div className="border-b border-border px-4 md:px-8">
        <Tabs value={section} onValueChange={handleTabChange}>
          <TabsList>
            {SECTIONS.map((s) => (
              <TabsTrigger key={s.key} value={s.key} className="text-xs">
                {s.label}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
      </div>

      <div className={`flex-1 min-h-0 ${section === "flow" ? "overflow-hidden" : "overflow-y-auto"} scrollbar-thin px-4 py-6 md:px-8`}>
        {section === "dashboard" && (
          <JourneyDashboard
            journey={journey}
            instances={instances}
            mappings={mappings}
            actionLoading={actionLoading}
            onAction={handleAction}
            onTestJourney={() => setTestOpen(true)}
            onOpenFlow={() => handleTabChange("flow")}
          />
        )}
        {section === "flow" && <FlowBuilder journeyId={id} journeyName={journey.name} />}
        {section === "running" && <RunningInstances instances={instances} onRefresh={fetchInstances} />}
        {section === "settings" && (
          <JourneySettings
            journey={journey}
            mappings={mappings}
            onRefreshMappings={() => {
              stageMappingService.list({ journeyId: id }).then(setMappings).catch(() => {});
            }}
          />
        )}
      </div>
    </>
  );

  const triggerLabel = triggerMapping?.stage_key || null;

  return (
    <div data-testid="page-journey-detail" className="flex h-full min-h-0 flex-col">
      <PageHeader
        title={journey.name}
        description={
          isDraft
            ? "Status: Draft · Set up your journey below"
            : `Status: ${journey.status}${triggerLabel ? ` · Trigger: ${triggerLabel}` : ""}`
        }
        actions={
          <div className="flex items-center gap-2">
            {!isDraft && (
              <Button size="sm" variant="outline" onClick={() => setTestOpen(true)}>
                <Play className="mr-2 h-3.5 w-3.5" /> Test Journey
              </Button>
            )}
            {journey.status === "draft" && (
              <Button size="sm" onClick={() => handleAction("activate")} disabled={actionLoading}>
                Activate
              </Button>
            )}
            {journey.status === "active" && (
              <>
                <Button size="sm" variant="outline" onClick={() => handleAction("pause")} disabled={actionLoading}>
                  Pause
                </Button>
                <Button size="sm" variant="outline" onClick={() => handleAction("archive")} disabled={actionLoading}>
                  Archive
                </Button>
              </>
            )}
            {journey.status === "paused" && (
              <>
                <Button size="sm" onClick={() => handleAction("activate")} disabled={actionLoading}>
                  Activate
                </Button>
                <Button size="sm" variant="outline" onClick={() => handleAction("archive")} disabled={actionLoading}>
                  Archive
                </Button>
              </>
            )}
            <Button size="sm" variant="destructive" onClick={() => setDeleteOpen(true)} disabled={actionLoading}>
              Delete
            </Button>
          </div>
        }
      />

      {isDraft ? renderWizard() : renderTabs()}

      <TestJourneyDialog open={testOpen} onOpenChange={setTestOpen} journeyId={id} />

      <Dialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Journey</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{journey.name}"? This action cannot be undone. All associated stage mappings and running instances will be removed.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteOpen(false)}>Cancel</Button>
            <Button variant="destructive" onClick={handleDelete} disabled={actionLoading}>Delete</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

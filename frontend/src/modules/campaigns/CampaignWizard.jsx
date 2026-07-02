import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { cn } from "@/lib/utils";
import { CheckCircle2, ChevronLeft, ChevronRight, Rocket, Sparkles } from "lucide-react";

const STEPS = [
  { id: 1, key: "template", label: "Select Template" },
  { id: 2, key: "audience", label: "Audience" },
  { id: 3, key: "schedule", label: "Schedule" },
  { id: 4, key: "review", label: "Review" },
  { id: 5, key: "launch", label: "Launch" },
];

export default function CampaignWizard({ open, onOpenChange, templates = [] }) {
  const [step, setStep] = useState(1);
  const [templateId, setTemplateId] = useState("");
  const [audience, setAudience] = useState("all");
  const [scheduleType, setScheduleType] = useState("now");
  const [scheduleDate, setScheduleDate] = useState("");
  const [name, setName] = useState("");

  const reset = () => {
    setStep(1);
    setTemplateId("");
    setAudience("all");
    setScheduleType("now");
    setScheduleDate("");
    setName("");
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) reset(); }}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>New campaign</DialogTitle>
          <DialogDescription>Broadcast an approved template to a chosen audience.</DialogDescription>
        </DialogHeader>

        <div className="flex items-center gap-1.5 border-b border-border pb-3">
          {STEPS.map((s, i) => {
            const active = s.id === step;
            const done = s.id < step;
            return (
              <div key={s.id} className="flex flex-1 items-center gap-1.5">
                <div className={cn("flex h-6 w-6 items-center justify-center rounded-full border text-[10px] font-bold", active ? "border-primary bg-primary text-primary-foreground" : done ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-600" : "border-border bg-secondary text-muted-foreground")}>
                  {done ? <CheckCircle2 className="h-3 w-3" /> : s.id}
                </div>
                <span className={cn("text-[11px]", active ? "font-semibold" : "text-muted-foreground")}>{s.label}</span>
                {i < STEPS.length - 1 && <span className="ml-1 h-px flex-1 bg-border" />}
              </div>
            );
          })}
        </div>

        <div className="min-h-[200px] py-4">
          {step === 3 && (
            <div className="space-y-4">
              <div className="space-y-1.5">
                <Label>When to send</Label>
                <Select value={scheduleType} onValueChange={setScheduleType}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
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
                  <Input type="datetime-local" value={scheduleDate} onChange={(e) => setScheduleDate(e.target.value)} />
                </div>
              )}
              <div className="space-y-1.5">
                <Label>Campaign name</Label>
                <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Campaign name" />
              </div>
            </div>
          )}

          {step === 5 && (
            <div className="flex flex-col items-center justify-center gap-3 py-8">
              <div className="flex h-14 w-14 items-center justify-center rounded-full bg-primary/10 text-primary">
                <Rocket className="h-6 w-6" />
              </div>
              <h3 className="text-lg font-bold">Ready to launch</h3>
              <p className="max-w-sm text-center text-sm text-muted-foreground">
                "{name}" will broadcast to your selected audience.
              </p>
            </div>
          )}
        </div>

        <DialogFooter className="flex-row items-center justify-between border-t border-border pt-3 sm:justify-between">
          <Button variant="ghost" size="sm" onClick={() => setStep(Math.max(1, step - 1))} disabled={step === 1}>
            <ChevronLeft className="mr-1 h-3.5 w-3.5" /> Back
          </Button>
          {step < 5 ? (
            <Button size="sm" onClick={() => setStep(step + 1)}>
              Next <ChevronRight className="ml-1 h-3.5 w-3.5" />
            </Button>
          ) : (
            <Button size="sm" onClick={reset}><Rocket className="mr-2 h-3.5 w-3.5" /> Launch campaign</Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

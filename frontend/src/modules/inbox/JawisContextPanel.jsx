import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Lock, Pause, Undo2, Sparkles, Phone, Mail } from "lucide-react";

function ContextField({ label, value }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="text-[11px] text-muted-foreground">{label}</span>
      <span className="truncate text-xs font-medium">{value}</span>
    </div>
  );
}

export default function JawisContextPanel({ selected }) {
  return (
    <aside className="hidden w-[300px] shrink-0 flex-col border-l border-border bg-card/30 xl:flex">
      <div className="p-5 text-center">
        <Avatar className="mx-auto h-16 w-16">
          <AvatarFallback className="bg-primary/10 text-lg font-semibold text-primary">
            {selected.initials}
          </AvatarFallback>
        </Avatar>
        <h3 className="mt-3 text-base font-bold">{selected.customer}</h3>
        <p className="text-xs text-muted-foreground">{selected.company}</p>
        <div className="mt-3 flex justify-center gap-1.5">
          <Button variant="outline" size="sm" className="h-7 text-xs"><Phone className="mr-1 h-3 w-3" /> Call</Button>
          <Button variant="outline" size="sm" className="h-7 text-xs"><Mail className="mr-1 h-3 w-3" /> Email</Button>
        </div>
      </div>
      <Separator />

      <div className="space-y-5 overflow-y-auto scrollbar-thin p-5 text-sm">
        <div>
          <div className="mb-3 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
            <Lock className="h-3 w-3 text-muted-foreground/70" />
            <span>JAWIS</span>
          </div>
          <div className="space-y-2 rounded-lg border border-border bg-card p-3">
            <ContextField label="Company" value={selected.company} />
            <ContextField label="Lead Stage" value={selected.stage} />
            <ContextField label="Owner" value={selected.assignee} />
          </div>
        </div>

        <div>
          <div className="mb-3 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
            Journey
          </div>
          <div className="rounded-lg border border-border bg-card p-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold">Visit Reminder</span>
              <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-600 dark:text-emerald-400">
                <span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-500" />
                Active
              </span>
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-1.5">
          <Button variant="outline" size="sm" className="h-8 justify-start text-xs"><Pause className="mr-2 h-3 w-3" /> Pause</Button>
          <Button variant="outline" size="sm" className="h-8 justify-start text-xs"><Undo2 className="mr-2 h-3 w-3" /> Override</Button>
          <Button variant="outline" size="sm" className="h-8 justify-start text-xs"><Sparkles className="mr-2 h-3 w-3" /> AI On/Off</Button>
        </div>
      </div>
    </aside>
  );
}

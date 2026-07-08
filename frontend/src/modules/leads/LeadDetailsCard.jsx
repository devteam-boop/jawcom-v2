import { Card } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { User } from "lucide-react";

/**
 * Lead Details card.
 *
 * NOTE: JawCom does not store or fetch lead PII (name/email/phone) — that
 * data belongs to JAWIS. There is no existing API route exposing it to the
 * frontend, and adding one is backend work explicitly out of scope for this
 * task ("No backend redesign", "No JAWIS changes"). This card shows what is
 * actually available today: the lead identifier plus facts derived from the
 * lead's own journey/communication data — the same "Lead #<id>" convention
 * already used in ExecutionDrawer.
 */
export default function LeadDetailsCard({ leadId, instanceCount, eventCount, lastActivityAt }) {
  return (
    <Card className="rounded-xl border-border bg-card p-5">
      <div className="flex items-start gap-4">
        <Avatar className="h-12 w-12">
          <AvatarFallback className="bg-primary/10 text-primary">
            <User className="h-5 w-5" />
          </AvatarFallback>
        </Avatar>
        <div className="min-w-0 flex-1">
          <h3 className="text-base font-semibold">Lead #{leadId}</h3>
          <p className="mt-0.5 text-xs text-muted-foreground">
            Name/email/phone are owned by JAWIS and not fetched here — see JawCom scaling rules.
          </p>
          <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
            <div>
              <div className="text-xs text-muted-foreground">Journeys</div>
              <div className="font-mono font-semibold">{instanceCount}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">Communication Events</div>
              <div className="font-mono font-semibold">{eventCount}</div>
            </div>
            <div className="col-span-2">
              <div className="text-xs text-muted-foreground">Last Activity</div>
              <div className="font-medium">{lastActivityAt ? new Date(lastActivityAt).toLocaleString() : "—"}</div>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
}

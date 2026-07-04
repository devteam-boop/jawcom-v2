import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import TriggerConfiguration from "./TriggerConfiguration";

export default function JourneySettings({ journey, mappings = [], onRefreshMappings }) {
  return (
    <div className="space-y-6">
      <TriggerConfiguration
        journeyId={journey?.id}
        mappings={mappings}
        onRefresh={onRefreshMappings}
      />

      <Separator />

      <Card className="rounded-xl border-border bg-card p-6">
        <h3 className="mb-4 text-sm font-bold">Retry Policy</h3>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <div className="space-y-1.5">
            <Label>Max Retries</Label>
            <Input type="number" defaultValue={3} />
          </div>
          <div className="space-y-1.5">
            <Label>Backoff (seconds)</Label>
            <Input type="number" defaultValue={60} />
          </div>
          <div className="space-y-1.5">
            <Label>Dead Letter Action</Label>
            <Select defaultValue="skip">
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="skip">Skip</SelectItem>
                <SelectItem value="pause">Pause</SelectItem>
                <SelectItem value="notify">Notify</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </Card>

      <Card className="rounded-xl border-border bg-card p-6">
        <h3 className="mb-4 text-sm font-bold">Business Hours</h3>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div className="space-y-1.5">
            <Label>Timezone</Label>
            <Select defaultValue="Asia/Kolkata">
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="Asia/Kolkata">Asia/Kolkata (IST)</SelectItem>
                <SelectItem value="America/New_York">America/New_York (EST)</SelectItem>
                <SelectItem value="Europe/London">Europe/London (GMT)</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label>Working Days</Label>
            <Select defaultValue="mon-fri">
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="mon-fri">Mon–Fri</SelectItem>
                <SelectItem value="mon-sat">Mon–Sat</SelectItem>
                <SelectItem value="all">All days</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label>Working Hours Start</Label>
            <Input type="time" defaultValue="09:00" />
          </div>
          <div className="space-y-1.5">
            <Label>Working Hours End</Label>
            <Input type="time" defaultValue="18:00" />
          </div>
        </div>
      </Card>

      <Card className="rounded-xl border-border bg-card p-6">
        <h3 className="mb-4 text-sm font-bold">Defaults</h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between rounded-lg border border-border p-3">
            <div>
              <div className="text-sm font-medium">Send outside business hours</div>
              <div className="text-xs text-muted-foreground">Queue messages until next working period</div>
            </div>
            <Switch defaultChecked />
          </div>
        </div>
      </Card>

      <div className="flex justify-end gap-2">
        <Button variant="outline">Cancel</Button>
        <Button>Save Settings</Button>
      </div>
    </div>
  );
}

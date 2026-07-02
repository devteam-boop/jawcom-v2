import PageHeader from "@/components/PageHeader";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { INTEGRATIONS } from "@/dummy-data";
import {
  MessageCircle,
  Facebook,
  Instagram,
  Globe,
  Mail,
  Sparkles,
  Cpu,
  Webhook,
  Code,
  Check,
} from "lucide-react";

const iconMap = {
  "WhatsApp Business": MessageCircle,
  "Facebook Messenger": Facebook,
  "Instagram DM": Instagram,
  "Google Business": Globe,
  Gmail: Mail,
  "Claude (Anthropic)": Sparkles,
  OpenAI: Cpu,
  Webhooks: Webhook,
  "REST API": Code,
};

export default function Integrations() {
  return (
    <div data-testid="page-integrations">
      <PageHeader
        title="Integrations"
        description="Connect JawCom to the channels and tools your team already uses."
      />

      <div className="px-4 py-6 md:px-8">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {INTEGRATIONS.map((i) => {
            const Icon = iconMap[i.name] || Globe;
            return (
              <Card
                key={i.id}
                className="rounded-xl border-border bg-card p-5 shadow-sm transition-colors hover:border-primary/30"
                data-testid={`integration-${i.id}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex h-11 w-11 items-center justify-center rounded-lg border border-border bg-secondary/60">
                    <Icon className="h-5 w-5" />
                  </div>
                  {i.connected ? (
                    <Badge variant="outline" className="bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-500/20 font-medium">
                      <Check className="mr-1 h-3 w-3" /> Connected
                    </Badge>
                  ) : (
                    <Badge variant="outline" className="font-medium">Not connected</Badge>
                  )}
                </div>

                <h3 className="mt-4 text-base font-bold">{i.name}</h3>
                <p className="mt-0.5 text-[11px] uppercase tracking-wider text-muted-foreground">{i.category}</p>
                <p className="mt-2 text-sm text-muted-foreground">{i.description}</p>

                <div className="mt-4 flex items-center justify-between border-t border-border pt-4">
                  <span className="text-xs text-muted-foreground">
                    {i.accounts > 0 ? `${i.accounts} account${i.accounts > 1 ? "s" : ""}` : "No accounts"}
                  </span>
                  <Button
                    size="sm"
                    variant={i.connected ? "outline" : "default"}
                    className="h-7 text-xs"
                    data-testid={`integration-action-${i.id}`}
                  >
                    {i.connected ? "Configure" : "Connect"}
                  </Button>
                </div>
              </Card>
            );
          })}
        </div>
      </div>
    </div>
  );
}

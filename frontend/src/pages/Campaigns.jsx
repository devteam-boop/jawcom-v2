import { useEffect, useState } from "react";
import PageHeader from "@/components/PageHeader";
import EmptyState from "@/components/EmptyState";
import LoadingSkeleton from "@/components/LoadingSkeleton";
import { campaignService } from "@/services/campaigns";
import { Megaphone } from "lucide-react";

/**
 * The dummy CAMPAIGNS list (and the 5-step "launch" wizard, which never
 * called any backend — it only reset local state on submit) have been
 * removed. campaignService already targets /api/campaigns, but no such
 * router is registered in backend/app/main.py — only the `campaigns` /
 * `campaign_recipients` SQLAlchemy models exist (backend/app/models/), with
 * no service/repository/routes layer built on top of them yet.
 *
 * campaignService.list() is still called here (rather than skipped) so this
 * page starts showing real data automatically the day that API exists — no
 * further frontend change needed. A full Campaigns rebuild (service layer +
 * routes + this UI) is Phase 2/3 work — see the audit report.
 */
export default function Campaigns() {
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [apiAvailable, setApiAvailable] = useState(true);

  useEffect(() => {
    let active = true;
    campaignService
      .list()
      .then((data) => { if (active) setCampaigns(data || []); })
      .catch(() => { if (active) setApiAvailable(false); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  return (
    <div data-testid="page-campaigns">
      <PageHeader
        title="Campaigns"
        description="Broadcast approved templates to your audiences."
      />

      <div className="space-y-5 px-4 py-6 md:px-8">
        {loading ? (
          <LoadingSkeleton rows={4} />
        ) : !apiAvailable ? (
          <EmptyState
            icon={Megaphone}
            title="No campaign engine yet"
            description="There is no backend API for campaigns (models exist, but no service/routes are wired up). This page will list real campaigns once that engine is built — see the audit report."
          />
        ) : campaigns.length === 0 ? (
          <EmptyState
            icon={Megaphone}
            title="No campaigns found"
            description="Campaigns you launch will appear here."
          />
        ) : (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
            {campaigns.map((c) => (
              <div key={c.id} className="rounded-xl border border-border bg-card p-5 shadow-sm">
                <h3 className="truncate text-base font-bold">{c.name}</h3>
                <p className="mt-1 text-xs text-muted-foreground">{c.status}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

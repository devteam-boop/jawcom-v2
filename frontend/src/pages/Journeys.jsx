import { useState, useEffect, useMemo } from "react";
import PageHeader from "@/components/PageHeader";
import { JourneyList } from "@/modules/journeys";
import { useJourneys } from "@/modules/journeys";
import { stageMappingService } from "@/services/stageMappings";
import { runningInstanceService } from "@/services/runningInstances";
import { journeyService } from "@/services/journeys";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function Journeys() {
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");
  const { journeys, loading, refetch } = useJourneys();
  const [mappings, setMappings] = useState([]);
  const [instanceCounts, setInstanceCounts] = useState({});
  const [createOpen, setCreateOpen] = useState(false);
  const [createName, setCreateName] = useState("");
  const [createDesc, setCreateDesc] = useState("");

  useEffect(() => {
    stageMappingService.list().then(setMappings).catch(() => {});
  }, []);

  useEffect(() => {
    if (!journeys.length) return;
    Promise.all(
      journeys.map(async (j) => {
        try {
          const instances = await runningInstanceService.list({ journeyId: j.id });
          return { id: j.id, count: instances.length };
        } catch {
          return { id: j.id, count: 0 };
        }
      })
    ).then((results) => {
      const map = {};
      results.forEach((r) => { map[r.id] = r.count; });
      setInstanceCounts(map);
    });
  }, [journeys]);

  const enriched = useMemo(() => {
    if (!journeys.length) return [];
    return journeys.map((j) => ({
      ...j,
      stageMappings: mappings.filter((sm) => sm.journey_id === j.id),
      runningCount: instanceCounts[j.id] || 0,
      health: null,
    }));
  }, [journeys, mappings, instanceCounts]);

  const handleCreate = async () => {
    if (!createName.trim()) return;
    try {
      await journeyService.create({
        name: createName.trim(),
        description: createDesc.trim() || null,
        trigger_type: "lead_stage_changed",
      });
      setCreateOpen(false);
      setCreateName("");
      setCreateDesc("");
      refetch();
    } catch (err) {
      console.error("Create failed", err);
    }
  };

  if (loading) {
    return (
      <div data-testid="page-journeys">
        <PageHeader title="Journeys" description="Manage your stage-to-flow mappings, flow builder, and running instances." />
        <div className="flex items-center justify-center p-12 text-sm text-muted-foreground">Loading journeys…</div>
      </div>
    );
  }

  return (
    <div data-testid="page-journeys">
      <PageHeader
        title="Journeys"
        description="Manage your stage-to-flow mappings, flow builder, and running instances."
      />
      <div className="space-y-4 px-4 py-6 md:px-8">
        <JourneyList
          journeys={enriched}
          search={search}
          onSearchChange={setSearch}
          filter={filter}
          onFilterChange={setFilter}
          onCreate={() => setCreateOpen(true)}
        />
      </div>

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Journey</DialogTitle>
            <DialogDescription>Define a new automated journey for your leads.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-1.5">
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                value={createName}
                onChange={(e) => setCreateName(e.target.value)}
                placeholder="e.g. Lead Qualification"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="desc">Description</Label>
              <Input
                id="desc"
                value={createDesc}
                onChange={(e) => setCreateDesc(e.target.value)}
                placeholder="Optional description"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>Cancel</Button>
            <Button onClick={handleCreate}>Create</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

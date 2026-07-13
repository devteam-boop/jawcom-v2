import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
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
import { toast } from "sonner";

export default function Journeys() {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");
  const { journeys, loading, refetch } = useJourneys();
  const [mappings, setMappings] = useState([]);
  const [instanceCounts, setInstanceCounts] = useState({});
  const [createOpen, setCreateOpen] = useState(false);
  const [createName, setCreateName] = useState("");
  const [createDesc, setCreateDesc] = useState("");
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

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

  const handleDuplicate = async (journey) => {
    try {
      await journeyService.duplicate(journey.id);
      toast.success(`Duplicated "${journey.name}"`);
      refetch();
    } catch (err) {
      toast.error(err?.message || "Failed to duplicate journey");
    }
  };

  const handleConfirmDelete = async () => {
    if (!deleteTarget) return;
    setDeleteLoading(true);
    try {
      await journeyService.delete(deleteTarget.id);
      toast.success(`Deleted "${deleteTarget.name}"`);
      setDeleteTarget(null);
      refetch();
    } catch (err) {
      toast.error(err?.message || "Failed to delete journey");
    } finally {
      setDeleteLoading(false);
    }
  };

  const isDeleteBlocked = deleteTarget?.status === "active";

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
          onEdit={(journey) => navigate(`/journeys/${journey.id}`)}
          onDuplicate={handleDuplicate}
          onDeleteRequest={setDeleteTarget}
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

      <Dialog open={!!deleteTarget} onOpenChange={(open) => !open && setDeleteTarget(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Journey?</DialogTitle>
            <DialogDescription>
              {isDeleteBlocked
                ? "Deactivate this journey before deleting."
                : "This will permanently delete the journey definition. Execution history and analytics will not be deleted."}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            {isDeleteBlocked ? (
              <Button onClick={() => setDeleteTarget(null)}>Cancel</Button>
            ) : (
              <>
                <Button variant="outline" onClick={() => setDeleteTarget(null)}>Cancel</Button>
                <Button variant="destructive" onClick={handleConfirmDelete} disabled={deleteLoading}>
                  Delete
                </Button>
              </>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

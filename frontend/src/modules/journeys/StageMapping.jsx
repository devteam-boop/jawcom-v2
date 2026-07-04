import { useState } from "react";
import { toast } from "sonner";
import { stageMappingService } from "@/services/stageMappings";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Plus, Pencil, Trash2, Zap, Loader2 } from "lucide-react";

const EMPTY_FORM = {
  name: "",
  description: "",
  stage_key: "",
  channel: "",
  template_id: "",
  sort_order: 0,
  config: "{}",
};

const CHANNELS = ["", "email", "whatsapp", "sms", "voice", "in-app"];

export default function StageMapping({ mappings = [], journeyId, onRefresh }) {
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [deleting, setDeleting] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);

  const resetForm = () => {
    setForm(EMPTY_FORM);
    setEditing(null);
  };

  const openCreate = () => {
    resetForm();
    setOpen(true);
  };

  const openEdit = (mapping) => {
    setForm({
      name: mapping.name || "",
      description: mapping.description || "",
      stage_key: mapping.stage_key || "",
      channel: mapping.channel || "",
      template_id: mapping.template_id || "",
      sort_order: mapping.sort_order ?? 0,
      config: mapping.config ? JSON.stringify(mapping.config, null, 2) : "{}",
    });
    setEditing(mapping);
    setOpen(true);
  };

  const handleSave = async () => {
    let config;
    try {
      config = JSON.parse(form.config);
    } catch {
      toast.error("Config must be valid JSON");
      return;
    }

    const payload = {
      journey_id: journeyId,
      name: form.name || undefined,
      description: form.description || undefined,
      stage_key: form.stage_key,
      channel: form.channel || undefined,
      template_id: form.template_id || undefined,
      sort_order: Number(form.sort_order),
      config,
    };

    if (!payload.stage_key) {
      toast.error("Stage Key is required");
      return;
    }

    setSaving(true);
    try {
      if (editing) {
        const updatePayload = { ...payload };
        delete updatePayload.journey_id;
        await stageMappingService.update(editing.id, updatePayload);
        toast.success("Stage mapping updated");
      } else {
        await stageMappingService.create(payload);
        toast.success("Stage mapping created");
      }
      setOpen(false);
      resetForm();
      if (onRefresh) onRefresh();
    } catch (err) {
      toast.error(err?.message || "Failed to save stage mapping");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!deleting) return;
    setSaving(true);
    try {
      await stageMappingService.delete(deleting.id);
      toast.success("Stage mapping deleted");
      setDeleting(null);
      if (onRefresh) onRefresh();
    } catch (err) {
      toast.error(err?.message || "Failed to delete stage mapping");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold">Stage Mappings</h3>
          <p className="text-xs text-muted-foreground">
            Map JAWIS lead stages to trigger this journey
          </p>
        </div>
        <Button size="sm" variant="outline" onClick={openCreate}>
          <Plus className="mr-2 h-3.5 w-3.5" /> Add mapping
        </Button>
      </div>

      {mappings.length === 0 ? (
        <Card className="rounded-xl border-dashed border-border bg-card p-6 text-center text-sm text-muted-foreground">
          <Zap className="mx-auto mb-2 h-5 w-5" />
          No stage mappings configured.
        </Card>
      ) : (
        <div className="space-y-2">
          {mappings.map((m) => (
            <Card
              key={m.id}
              className="flex items-center justify-between rounded-xl border-border bg-card p-4"
            >
              <div className="flex min-w-0 flex-1 items-center gap-4">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold">
                      {m.name || m.stage_key}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      ({m.stage_key})
                    </span>
                  </div>
                  <div className="mt-0.5 flex flex-wrap gap-2 text-xs text-muted-foreground">
                    {m.channel && (
                      <span className="rounded-md border border-border bg-background px-1.5 py-0.5">
                        {m.channel}
                      </span>
                    )}
                    <span>Order: {m.sort_order ?? 0}</span>
                    {m.template_id && (
                      <span className="truncate max-w-[120px]" title={m.template_id}>
                        Template: {m.template_id.slice(0, 8)}...
                      </span>
                    )}
                  </div>
                </div>
              </div>
              <div className="flex shrink-0 items-center gap-1">
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => openEdit(m)}
                >
                  <Pencil className="h-3.5 w-3.5" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 text-destructive hover:text-destructive"
                  onClick={() => setDeleting(m)}
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      <Dialog open={open} onOpenChange={(v) => { if (!v) { setOpen(false); resetForm(); } }}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>{editing ? "Edit" : "Add"} Stage Mapping</DialogTitle>
            <DialogDescription>
              {editing
                ? "Update the stage mapping fields below."
                : "Configure a new stage mapping for this journey."}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-2">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label>Name</Label>
                <Input
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="e.g. Qualified Lead Entry"
                />
              </div>
              <div className="space-y-1.5">
                <Label>Stage Key *</Label>
                <Input
                  value={form.stage_key}
                  onChange={(e) => setForm({ ...form, stage_key: e.target.value })}
                  placeholder="e.g. qualified"
                />
              </div>
            </div>
            <div className="space-y-1.5">
              <Label>Description</Label>
              <Textarea
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                placeholder="Optional description"
                rows={2}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label>Channel</Label>
                <Select
                  value={form.channel}
                  onValueChange={(v) => setForm({ ...form, channel: v })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select channel" />
                  </SelectTrigger>
                  <SelectContent>
                    {CHANNELS.map((c) => (
                      <SelectItem key={c} value={c}>
                        {c || "None"}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label>Sort Order</Label>
                <Input
                  type="number"
                  value={form.sort_order}
                  onChange={(e) =>
                    setForm({ ...form, sort_order: parseInt(e.target.value) || 0 })
                  }
                />
              </div>
            </div>
            <div className="space-y-1.5">
              <Label>Template ID (optional)</Label>
              <Input
                value={form.template_id}
                onChange={(e) => setForm({ ...form, template_id: e.target.value })}
                placeholder="UUID of template"
              />
            </div>
            <div className="space-y-1.5">
              <Label>Config (JSON)</Label>
              <Textarea
                value={form.config}
                onChange={(e) => setForm({ ...form, config: e.target.value })}
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => { setOpen(false); resetForm(); }}
            >
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={saving}>
              {saving && <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" />}
              {editing ? "Update" : "Create"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={!!deleting} onOpenChange={(v) => { if (!v) setDeleting(null); }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Stage Mapping</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{deleting?.name || deleting?.stage_key}"?
              This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleting(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={saving}
            >
              {saving && <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" />}
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

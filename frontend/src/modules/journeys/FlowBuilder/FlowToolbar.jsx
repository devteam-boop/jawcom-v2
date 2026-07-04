import { Button } from "@/components/ui/button";
import { Save, UploadCloud, CheckCircle2, Loader2 } from "lucide-react";

export default function FlowToolbar({
  journeyName,
  onSave,
  onValidate,
  onPublish,
  saving,
  publishing,
}) {
  return (
    <div className="flex items-center justify-between border-b border-border bg-card px-6 py-3">
      <div className="flex items-center gap-2">
        <h2 className="text-sm font-bold">{journeyName}</h2>
      </div>
      <div className="flex items-center gap-2">
        <Button variant="outline" size="sm" onClick={onValidate}>
          <CheckCircle2 className="mr-2 h-3.5 w-3.5" /> Validate
        </Button>
        <Button variant="outline" size="sm" onClick={onSave} disabled={saving || publishing}>
          {saving ? <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" /> : <Save className="mr-2 h-3.5 w-3.5" />}
          Save
        </Button>
        <Button size="sm" onClick={onPublish} disabled={saving || publishing}>
          {publishing ? <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" /> : <UploadCloud className="mr-2 h-3.5 w-3.5" />}
          Publish
        </Button>
      </div>
    </div>
  );
}

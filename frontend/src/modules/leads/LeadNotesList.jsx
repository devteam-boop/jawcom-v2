import { useMemo } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import EmptyState from "@/components/EmptyState";
import { formatDateTimeWithRelative } from "@/lib/dateFormat";
import { StickyNote, ExternalLink } from "lucide-react";

/**
 * Notes derived from the lead's own communication-event stream
 * (event_type === "note_added"). There is no separate Notes API/table in
 * JawCom — note content only exists as CommunicationEvent.payload.
 * This is a filtered *view* of the same events CommunicationTimeline
 * already renders, not a second, competing timeline.
 */
export default function LeadNotesList({ events = [], onOpenInstance }) {
  const notes = useMemo(
    () =>
      events
        .filter((e) => e.event_type === "note_added")
        .map((e) => ({
          id: e.id,
          text: e.payload?.resolved_note || e.payload?.note || "(empty note)",
          occurred_at: e.occurred_at,
          running_instance_id: e.running_instance_id,
        }))
        .sort((a, b) => new Date(b.occurred_at) - new Date(a.occurred_at)),
    [events]
  );

  if (notes.length === 0) {
    return (
      <EmptyState
        icon={StickyNote}
        title="No notes yet"
        description="Notes created by a journey's Create Note node will appear here."
      />
    );
  }

  return (
    <div className="space-y-2">
      {notes.map((note) => (
        <Card key={note.id} className="rounded-lg border-border p-3">
          <div className="flex items-start justify-between gap-2">
            <div className="flex items-start gap-2 text-sm">
              <StickyNote className="mt-0.5 h-4 w-4 shrink-0 text-amber-500" />
              <span>{note.text}</span>
            </div>
            {onOpenInstance && note.running_instance_id && (
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6 shrink-0"
                onClick={() => onOpenInstance(note.running_instance_id)}
                title="View journey instance"
              >
                <ExternalLink className="h-3.5 w-3.5" />
              </Button>
            )}
          </div>
          <div className="mt-1.5 text-xs text-muted-foreground">
            {formatDateTimeWithRelative(note.occurred_at)}
          </div>
        </Card>
      ))}
    </div>
  );
}

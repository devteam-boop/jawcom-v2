import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { Paperclip, Smile, Mic, Send, Sparkles } from "lucide-react";

export default function MessageComposer({ recipientName, channel }) {
  return (
    <div className="border-t border-border bg-background p-4">
      <div className="rounded-xl border border-border bg-card focus-within:border-primary/40 focus-within:ring-2 focus-within:ring-primary/10">
        <Textarea
          placeholder={`Reply to ${recipientName} on ${channel}…`}
          rows={2}
          className="resize-none border-0 bg-transparent text-sm focus-visible:ring-0 focus-visible:ring-offset-0"
        />
        <div className="flex items-center justify-between border-t border-border/60 px-2 py-1.5">
          <div className="flex items-center gap-0.5">
            <Button variant="ghost" size="icon" className="h-7 w-7"><Paperclip className="h-4 w-4" /></Button>
            <Button variant="ghost" size="icon" className="h-7 w-7"><Smile className="h-4 w-4" /></Button>
            <Button variant="ghost" size="icon" className="h-7 w-7"><Mic className="h-4 w-4" /></Button>
            <Separator orientation="vertical" className="mx-1 h-4" />
            <Button variant="ghost" size="sm" className="h-7 px-2 text-xs">
              <Sparkles className="mr-1 h-3 w-3 text-primary" />
              AI draft
            </Button>
          </div>
          <Button size="sm" className="h-7">
            <Send className="mr-1 h-3 w-3" /> Send
          </Button>
        </div>
      </div>
    </div>
  );
}

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Sparkles, Zap, Phone, Video, MoreHorizontal } from "lucide-react";

export default function ConversationThread({ selected, messages }) {
  return (
    <section className="flex min-w-0 flex-1 flex-col">
      <div className="flex items-center justify-between border-b border-border p-4">
        <div className="flex items-center gap-3">
          <Avatar className="h-10 w-10">
            <AvatarFallback className="bg-primary/10 text-xs font-semibold text-primary">
              {selected.initials}
            </AvatarFallback>
          </Avatar>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold">{selected.customer}</h3>
              <span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-500" />
              <span className="text-xs text-muted-foreground">Online · {selected.channel}</span>
            </div>
            <p className="text-xs text-muted-foreground">{selected.company}</p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="icon" className="h-8 w-8"><Phone className="h-4 w-4" /></Button>
          <Button variant="ghost" size="icon" className="h-8 w-8"><Video className="h-4 w-4" /></Button>
          <Button variant="ghost" size="icon" className="h-8 w-8"><MoreHorizontal className="h-4 w-4" /></Button>
        </div>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto scrollbar-thin bg-secondary/20 p-6">
        {messages.map((m) => {
          if (m.from === "ai") {
            return (
              <div key={m.id} className="mx-auto max-w-xl rounded-xl border border-primary/30 bg-primary/5 p-3">
                <div className="mb-1 flex items-center gap-1.5 text-xs font-semibold text-primary">
                  <Sparkles className="h-3 w-3" />
                  AI Assistant · suggested reply
                </div>
                <p className="text-sm">{m.text}</p>
                <div className="mt-2 flex gap-1.5">
                  <Button size="sm" className="h-7 text-xs">Use</Button>
                  <Button size="sm" variant="ghost" className="h-7 text-xs">Edit</Button>
                </div>
              </div>
            );
          }
          const isAgent = m.from === "agent";
          return (
            <div key={m.id} className={cn("flex gap-2", isAgent ? "justify-end" : "justify-start")}>
              {!isAgent && (
                <Avatar className="h-7 w-7 shrink-0">
                  <AvatarFallback className="bg-secondary text-[10px] font-semibold">{selected.initials}</AvatarFallback>
                </Avatar>
              )}
              <div className={cn("max-w-[70%]", isAgent && "text-right")}>
                <div className={cn("rounded-2xl px-4 py-2.5 text-sm shadow-sm", isAgent ? "rounded-br-md bg-primary text-primary-foreground" : "rounded-bl-md border border-border bg-card")}>
                  {m.text}
                </div>
                {m.isAutoSent && (
                  <div className={cn("mt-1 inline-flex items-center gap-1 rounded-md bg-secondary px-1.5 py-0.5 text-[11px] font-medium text-muted-foreground", isAgent && "ml-auto")}>
                    <Zap className="h-2.5 w-2.5" />
                    <span>{m.journey}</span>
                    <span className="text-muted-foreground/60">·</span>
                    <span>auto-sent</span>
                  </div>
                )}
                <span className="mt-1 block text-[10px] text-muted-foreground">{m.time}</span>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

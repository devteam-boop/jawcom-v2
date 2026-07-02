import { useState } from "react";
import PageHeader from "@/components/PageHeader";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";
import { AI_MEMORY, AI_KNOWLEDGE_USAGE } from "@/dummy-data/ai-memory";
import {
  Sparkles,
  Send,
  Plus,
  Star,
  MessageSquarePlus,
  BookOpen,
  Brain,
  User,
  MessageSquare,
  ArrowRight,
  Wand2,
  Languages,
  Pencil,
  Reply,
  FileText,
  Megaphone,
  Trash2,
} from "lucide-react";

const HISTORY = [
  { id: "h1", title: "Draft renewal reminder for Growth accounts", when: "2m ago", pinned: false },
  { id: "h2", title: "Summarize today's inbox", when: "38m ago", pinned: false },
  { id: "h3", title: "Which leads are most likely to convert?", when: "1h ago", pinned: true },
  { id: "h4", title: "Rewrite proposal follow-up in casual tone", when: "3h ago", pinned: false },
  { id: "h5", title: "Translate FAQ to Hindi", when: "Yesterday", pinned: false },
  { id: "h6", title: "Objection handling script for pricing", when: "Yesterday", pinned: true },
  { id: "h7", title: "Draft campaign copy for Spring Promo", when: "2d ago", pinned: false },
];

const SAVED_PROMPTS = [
  { id: "sp1", label: "Book a meeting", body: "Draft a reply that offers 3 slots this week for a 30-min call." },
  { id: "sp2", label: "Objection: pricing", body: "Respond to a pricing objection using our value framing." },
  { id: "sp3", label: "Renewal nudge", body: "Warm renewal reminder — 30 days out, loyalty discount." },
  { id: "sp4", label: "Post-demo recap", body: "Recap the demo with next steps and links." },
];

const CHAT = [
  { id: "m1", from: "user", text: "Show me hot leads for today and draft a follow-up for the top 3." },
  { id: "m2", from: "ai", text: "Top 3 hot leads today: Priya Sharma (92%), Daniel Chen (86%), Sofia Rossi (81%). Here are draft replies tailored to each thread — I've referenced pricing.md and the analytics-module Loom.", refs: 3 },
  { id: "m3", from: "user", text: "Rewrite Sofia's reply in a warmer tone with less jargon." },
  { id: "m4", from: "ai", text: "Warmer version: \"Hey Sofia — sharing the integration docs again below. Let me know which section feels unclear and I'll walk you through it live 🙂 — happy to hop on 15 min today.\"", refs: 1 },
];

const AI_TOOLS = [
  { id: "t1", label: "Summarize", icon: FileText },
  { id: "t2", label: "Translate", icon: Languages },
  { id: "t3", label: "Rewrite", icon: Pencil },
  { id: "t4", label: "Reply", icon: Reply },
  { id: "t5", label: "Generate Template", icon: MessageSquarePlus },
  { id: "t6", label: "Generate Campaign", icon: Megaphone },
];

const NEXT_BEST_ACTIONS = [
  "Send proposal to Priya Sharma — she's 92% likely to convert this week.",
  "Reactivate Diego Alvarez — last engaged 14 days ago.",
  "Book demo with Hana Park — replied positively on pricing.",
];

export default function Assistant() {
  const [prompt, setPrompt] = useState("");

  return (
    <div data-testid="page-assistant" className="flex h-full min-h-0 flex-col">
      <PageHeader
        title="AI Assistant"
        description="Your workspace copilot — grounded in your knowledge base."
      />

      <div className="grid min-h-0 flex-1 grid-cols-1 lg:grid-cols-[260px_1fr_320px]">
        {/* LEFT: History + Saved prompts */}
        <aside className="flex flex-col overflow-y-auto scrollbar-thin border-r border-border bg-card/40 p-3" data-testid="assistant-left">
          <Button size="sm" className="mb-3 w-full" data-testid="assistant-new-chat">
            <Plus className="mr-2 h-3.5 w-3.5" /> New chat
          </Button>

          <div className="mb-1 px-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">History</div>
          <ul className="space-y-0.5">
            {HISTORY.map((h) => (
              <li key={h.id}>
                <button className="flex w-full items-start gap-2 rounded-md px-2 py-1.5 text-left text-xs hover:bg-secondary" data-testid={`hist-${h.id}`}>
                  {h.pinned && <Star className="mt-0.5 h-3 w-3 shrink-0 fill-amber-500 text-amber-500" />}
                  <div className="min-w-0 flex-1">
                    <div className="truncate">{h.title}</div>
                    <div className="text-[10px] text-muted-foreground">{h.when}</div>
                  </div>
                </button>
              </li>
            ))}
          </ul>

          <div className="mb-1 mt-5 px-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Saved prompts</div>
          <ul className="space-y-1">
            {SAVED_PROMPTS.map((p) => (
              <li key={p.id}>
                <button
                  onClick={() => setPrompt(p.body)}
                  className="flex w-full flex-col rounded-md border border-border bg-background p-2 text-left hover:border-primary/40"
                  data-testid={`prompt-${p.id}`}
                >
                  <span className="text-xs font-semibold">{p.label}</span>
                  <span className="line-clamp-2 text-[10px] text-muted-foreground">{p.body}</span>
                </button>
              </li>
            ))}
          </ul>
        </aside>

        {/* CENTER: Chat */}
        <main className="flex min-w-0 flex-col overflow-hidden" data-testid="assistant-chat">
          <div className="flex-1 space-y-4 overflow-y-auto scrollbar-thin bg-secondary/20 p-6">
            {CHAT.map((m) => {
              const isUser = m.from === "user";
              return (
                <div key={m.id} className={cn("flex gap-3", isUser ? "justify-end" : "justify-start")} data-testid={`chat-${m.id}`}>
                  {!isUser && (
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                      <Sparkles className="h-4 w-4" />
                    </div>
                  )}
                  <div className={cn("max-w-[68%]", isUser && "text-right")}>
                    <div className={cn(
                      "rounded-2xl px-4 py-2.5 text-sm shadow-sm",
                      isUser ? "rounded-br-md bg-primary text-primary-foreground" : "rounded-bl-md border border-border bg-card"
                    )}>
                      {m.text}
                    </div>
                    {m.refs && (
                      <span className="mt-1 inline-flex items-center gap-1 rounded-md bg-secondary px-1.5 py-0.5 text-[10px] text-muted-foreground">
                        <BookOpen className="h-2.5 w-2.5" /> Referenced {m.refs} source{m.refs > 1 ? "s" : ""}
                      </span>
                    )}
                  </div>
                  {isUser && (
                    <Avatar className="h-8 w-8">
                      <AvatarFallback className="bg-secondary text-[11px] font-semibold">MI</AvatarFallback>
                    </Avatar>
                  )}
                </div>
              );
            })}
          </div>

          {/* Suggested actions */}
          <div className="border-t border-border bg-background px-4 pt-3">
            <div className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Suggested actions</div>
            <div className="flex flex-wrap gap-1.5">
              {[
                "Send drafts to inbox",
                "Save as template",
                "Assign to Rohan",
                "Create follow-up task",
                "Draft campaign",
              ].map((s) => (
                <button key={s} className="rounded-full border border-border bg-secondary/50 px-3 py-1 text-xs text-muted-foreground hover:text-foreground" data-testid={`suggest-${s}`}>
                  {s}
                </button>
              ))}
            </div>
          </div>

          {/* Prompt box */}
          <div className="border-t border-border bg-background p-4">
            <div className="rounded-xl border border-border bg-card focus-within:border-primary/40 focus-within:ring-2 focus-within:ring-primary/10">
              <Textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Ask JawCom AI…"
                rows={2}
                className="resize-none border-0 bg-transparent text-sm focus-visible:ring-0 focus-visible:ring-offset-0"
                data-testid="assistant-prompt"
              />
              <div className="flex items-center justify-between border-t border-border/60 px-2 py-1.5">
                <div className="flex flex-wrap items-center gap-1">
                  {AI_TOOLS.map((t) => {
                    const Icon = t.icon;
                    return (
                      <Button key={t.id} variant="ghost" size="sm" className="h-7 px-2 text-xs" data-testid={`tool-${t.id}`}>
                        <Icon className="mr-1 h-3 w-3 text-primary" /> {t.label}
                      </Button>
                    );
                  })}
                </div>
                <Button size="sm" className="h-7" data-testid="assistant-send">
                  <Send className="mr-1 h-3 w-3" /> Send
                </Button>
              </div>
            </div>
          </div>
        </main>

        {/* RIGHT: Context + tools */}
        <aside className="overflow-y-auto scrollbar-thin border-l border-border bg-card/40 p-5 text-sm" data-testid="assistant-right">
          {/* Confidence */}
          <Card className="mb-4 rounded-lg border-primary/30 bg-primary/5 p-3">
            <div className="mb-1 flex items-center gap-1.5 text-xs font-semibold text-primary">
              <Sparkles className="h-3 w-3" /> Confidence score
            </div>
            <div className="mt-1 flex items-baseline gap-2">
              <span className="font-mono text-2xl font-semibold text-primary">89%</span>
              <span className="text-[11px] text-muted-foreground">high confidence</span>
            </div>
            <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-primary/10">
              <div className="h-full rounded-full bg-primary" style={{ width: "89%" }} />
            </div>
          </Card>

          <SectionTitle icon={BookOpen}>Knowledge used</SectionTitle>
          <ul className="mb-4 space-y-1">
            {AI_KNOWLEDGE_USAGE.map((u) => (
              <li key={u.id} className="flex items-center justify-between rounded-md border border-border p-2">
                <div className="min-w-0">
                  <div className="truncate text-xs font-medium">{u.source}</div>
                  <div className="text-[10px] text-muted-foreground">{u.lastUsed}</div>
                </div>
                <span className="font-mono text-[10px] font-semibold text-muted-foreground">{u.hits}</span>
              </li>
            ))}
          </ul>

          <SectionTitle icon={Brain}>Memory used</SectionTitle>
          <ul className="mb-4 space-y-1">
            {AI_MEMORY.slice(0, 4).map((m) => (
              <li key={m.id} className="rounded-md border border-border p-2">
                <div className="text-xs font-semibold">{m.label}</div>
                <p className="line-clamp-2 text-[10px] text-muted-foreground">{m.value}</p>
              </li>
            ))}
          </ul>

          <SectionTitle icon={User}>Customer context</SectionTitle>
          <div className="mb-4 rounded-md border border-border p-2 text-xs">
            <Row label="Customer" value="Priya Sharma" />
            <Row label="Company" value="Lumen Studio" />
            <Row label="Stage" value="Proposal" />
            <Row label="Owner" value="Maya Iyer" />
          </div>

          <SectionTitle icon={MessageSquare}>Conversation context</SectionTitle>
          <div className="mb-4 rounded-md border border-border p-2 text-xs">
            <Row label="Channel" value="WhatsApp" />
            <Row label="Last message" value="2m ago" />
            <Row label="Sentiment" value="Positive · 84%" />
            <Row label="Auto-sent" value="2 of 6" />
          </div>

          <SectionTitle icon={ArrowRight}>Next best action</SectionTitle>
          <ul className="mb-4 space-y-1.5">
            {NEXT_BEST_ACTIONS.map((n, i) => (
              <li key={i} className="rounded-md border border-border bg-background p-2 text-xs">{n}</li>
            ))}
          </ul>

          <div className="flex justify-between text-[10px] text-muted-foreground">
            <span>Grounded in {AI_KNOWLEDGE_USAGE.length + AI_MEMORY.length} sources</span>
            <button className="inline-flex items-center gap-1 text-muted-foreground hover:text-foreground">
              <Trash2 className="h-2.5 w-2.5" /> Clear context
            </button>
          </div>
        </aside>
      </div>
    </div>
  );
}

function SectionTitle({ icon: Icon, children }) {
  return (
    <div className="mb-1.5 flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
      <Icon className="h-3 w-3" /> {children}
    </div>
  );
}

function Row({ label, value }) {
  return (
    <div className="flex items-center justify-between border-b border-border/60 py-1 last:border-b-0">
      <span className="text-[11px] text-muted-foreground">{label}</span>
      <span className="text-xs font-medium">{value}</span>
    </div>
  );
}

import { useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Send, Paperclip, Smile, Sparkles, Wand2, Scissors, Briefcase, Smile as SmileyIcon, Languages, Lock, MessageCircle as MessageCircleIcon } from "lucide-react";
import { templateService } from "@/services/templates";
import { whatsappTemplateService } from "@/services/whatsappTemplates";
import { messageService } from "@/services/messages";
import { aiTextService } from "@/services/aiText";
import { aiAssistantService } from "@/services/aiAssistant";
import { aiSummaryService } from "@/services/aiSummary";
import { toast } from "sonner";

const TRANSLATE_LANGUAGES = ["Spanish", "Hindi", "French", "Arabic", "Portuguese"];

function extractVars(text = "", pattern) {
  const set = new Set();
  const re = new RegExp(pattern, "g");
  let m;
  while ((m = re.exec(text)) !== null) set.add(m[1]);
  return Array.from(set);
}

const CUSTOM = "__custom__";

/**
 * Real, live composer — reuses the existing production send endpoints
 * (POST /api/messages/email/send, POST /api/messages/whatsapp/send) with
 * module="general", context_id=null (a manual, non-journey send). Every
 * successful send lands in the same communication_events table a journey
 * send would, source="manual".
 *
 * Sending requires the logged-in admin session — those routes accept
 * either JAWIS's own bearer token or a valid admin session cookie (see
 * backend/app/core/jawis_auth_middleware.py). No secondary passcode: the
 * browser's session cookie (set at /login) covers every send, same as
 * every other authenticated route in the app.
 *
 * WhatsApp: outside the 24h customer-service session window (no inbound
 * reply yet, or more than 24h since the last one — see waWindow, computed
 * by ConversationThread from the same communication_events via
 * whatsappWindow.js) only an approved template may be sent — Meta's Cloud
 * API rejects freeform text outside an active session. Once waWindow.active
 * is true (a real inbound "replied" event within the last 24h), the
 * WhatsApp panel switches to Live Chat mode: template selector hidden,
 * plain text send instead, via POST /api/messages/whatsapp/send with
 * body set (no template_name/template_key) — backend/app/api/message_routes.py
 * re-checks the same 24h window server-side before calling
 * MetaProvider.send_message() (Graph API plain-text send). Email supports
 * both a template and a fully custom subject/body, unchanged.
 *
 * Attachments/emoji/voice are stubbed (disabled, tooltip'd) — no upload/
 * media backend exists.
 */
export default function MessageComposer({ leadId, leadStage, onSent, waWindow }) {
  const waWindowActive = !!waWindow?.active;
  const [channel, setChannel] = useState("email");
  const [emailTemplates, setEmailTemplates] = useState([]);
  const [waTemplates, setWaTemplates] = useState([]);
  const [templateId, setTemplateId] = useState(CUSTOM);
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [variables, setVariables] = useState({});
  const [sending, setSending] = useState(false);
  // Live Chat mode's freeform WhatsApp draft — separate from `body` (the
  // email custom-message field) since the two channels can hold independent
  // in-progress drafts.
  const [waFreeText, setWaFreeText] = useState("");

  const [aiBusy, setAiBusy] = useState(null); // which action is in flight, or null
  const [aiResult, setAiResult] = useState(null); // { title, text } shown in a dialog
  const [translateLang, setTranslateLang] = useState(TRANSLATE_LANGUAGES[0]);

  useEffect(() => {
    templateService.list({ channel: "email", status: "active" }).then(setEmailTemplates).catch(() => setEmailTemplates([]));
    whatsappTemplateService.list({ status: "APPROVED" }).then(setWaTemplates).catch(() => setWaTemplates([]));
  }, []);

  useEffect(() => {
    setTemplateId(CUSTOM);
    setSubject("");
    setBody("");
    setVariables({});
    setWaFreeText("");
  }, [channel, leadId]);

  const selectedEmailTemplate = useMemo(
    () => emailTemplates.find((t) => t.id === templateId) || null,
    [emailTemplates, templateId]
  );
  const selectedWaTemplate = useMemo(
    () => waTemplates.find((t) => t.id === templateId) || null,
    [waTemplates, templateId]
  );

  const emailVars = useMemo(
    () => (selectedEmailTemplate ? extractVars(`${selectedEmailTemplate.subject || ""}\n${selectedEmailTemplate.content || ""}`, "\\{\\{(\\w+)\\}\\}") : []),
    [selectedEmailTemplate]
  );
  const waVars = useMemo(
    () => (selectedWaTemplate ? extractVars(selectedWaTemplate.body || "", "\\{\\{\\s*(\\d+)\\s*\\}\\}") : []),
    [selectedWaTemplate]
  );

  const setVar = (key, value) => setVariables((v) => ({ ...v, [key]: value }));

  // AI Reply / Summarize conversation / Generate follow-up all read the
  // lead's existing communication history via the already-built AI Lead
  // Assistant / AI Summary endpoints — no new backend code. Rewrite/
  // Shorten/Translate/tone-change transform the agent's own draft text via
  // the one new endpoint (POST /api/ai/transform, Phase 3's minimal
  // addition). All correctly surface "not configured" when ANTHROPIC_API_KEY
  // is unset rather than faking a response.
  const runAi = async (action, fn) => {
    setAiBusy(action);
    try {
      await fn();
    } catch (err) {
      toast.error(err?.body?.detail || err.message || "AI request failed");
    } finally {
      setAiBusy(null);
    }
  };

  const handleAiReply = () =>
    runAi("reply", async () => {
      const result = await aiAssistantService.get(leadId);
      if (!result.reply_suggestion) {
        toast.info("No reply suggestion available for this conversation right now.");
        return;
      }
      setChannel("email");
      setTemplateId(CUSTOM);
      setBody(result.reply_suggestion);
    });

  const handleFollowUp = () =>
    runAi("followup", async () => {
      const result = await aiAssistantService.get(leadId);
      setAiResult({ title: "Suggested next action", text: `${result.next_best_action}\n\n${result.next_best_action_reason || ""}`.trim() });
    });

  const handleSummarize = () =>
    runAi("summarize", async () => {
      const result = await aiSummaryService.get(leadId);
      if (result.status === "ai_unavailable") {
        toast.error("AI Summary not configured (missing ANTHROPIC_API_KEY)");
        return;
      }
      setAiResult({ title: "Conversation summary", text: (result.summary || []).join("\n") || JSON.stringify(result) });
    });

  const handleDraftTransform = (action, lang) =>
    runAi(action, async () => {
      if (!body.trim()) return;
      const result = await aiTextService.transform(body, action, lang);
      setBody(result.text);
    });

  // Live Chat mode only (channel === "whatsapp" && waWindowActive) — offered
  // once the customer has actually replied, per spec. Every one of these
  // only inserts into the WhatsApp draft textbox; none of them sends.
  const handleWaSuggested = () =>
    runAi("wa-suggested", async () => {
      const result = await aiAssistantService.get(leadId);
      if (!result.reply_suggestion) {
        toast.info("No reply suggestion available for this conversation right now.");
        return;
      }
      setWaFreeText(result.reply_suggestion);
    });

  const handleWaTransform = (action, lang) =>
    runAi(action, async () => {
      if (!waFreeText.trim()) return;
      const result = await aiTextService.transform(waFreeText, action, lang);
      setWaFreeText(result.text);
    });

  const contentReady =
    !!leadStage &&
    (channel === "email"
      ? templateId === CUSTOM
        ? subject.trim() && body.trim()
        : true
      : waWindowActive
        ? waFreeText.trim().length > 0
        : !!selectedWaTemplate && waVars.every((v) => (variables[v] || "").trim()));

  const doSend = async () => {
    setSending(true);
    try {
      if (channel === "email") {
        const payload =
          templateId === CUSTOM
            ? { lead_id: leadId, template_key: null, stage: leadStage, module: "general", variables: { subject, body } }
            : { lead_id: leadId, template_key: templateId, stage: leadStage, module: "general", variables };
        const result = await messageService.sendEmail(payload);
        onSent?.({
          id: result.communication_event_id,
          event_type: "email_sent",
          channel: "email",
          lead_id: leadId,
          occurred_at: new Date().toISOString(),
          payload: {
            source: "manual",
            status: result.status,
            subject: templateId === CUSTOM ? subject : selectedEmailTemplate?.subject,
            body: templateId === CUSTOM ? body : selectedEmailTemplate?.content,
          },
        });
      } else if (waWindowActive) {
        // Live Chat mode — freeform reply, only Meta-acceptable (and only
        // offered here) within the 24h customer-service session window.
        const payload = {
          lead_id: leadId,
          body: waFreeText,
          stage: leadStage,
          module: "general",
        };
        const result = await messageService.sendWhatsapp(payload);
        onSent?.({
          id: result.communication_event_id,
          event_type: "whatsapp_sent",
          channel: "whatsapp",
          lead_id: leadId,
          occurred_at: new Date().toISOString(),
          payload: { source: "manual", status: result.status, body: waFreeText },
        });
      } else {
        const payload = {
          lead_id: leadId,
          template_name: selectedWaTemplate.template_name,
          language: selectedWaTemplate.language,
          stage: leadStage,
          module: "general",
          variables,
        };
        const result = await messageService.sendWhatsapp(payload);
        onSent?.({
          id: result.communication_event_id,
          event_type: "whatsapp_sent",
          channel: "whatsapp",
          lead_id: leadId,
          occurred_at: new Date().toISOString(),
          payload: { source: "manual", status: result.status, body: selectedWaTemplate.body },
        });
      }
      toast.success("Message sent");
      setTemplateId(CUSTOM);
      setSubject("");
      setBody("");
      setVariables({});
      setWaFreeText("");
    } catch (err) {
      toast.error(err?.body?.detail || err.message || "Send failed");
    } finally {
      setSending(false);
    }
  };

  const handleSend = async () => {
    if (!contentReady || sending) return;
    await doSend();
  };

  return (
    <div className="border-t border-border bg-background p-4" data-testid="message-composer">
      <div className="mb-2 flex items-center gap-1.5">
        <Button
          type="button"
          size="sm"
          variant={channel === "email" ? "default" : "outline"}
          className="h-7 text-xs"
          onClick={() => setChannel("email")}
          data-testid="composer-channel-email"
        >
          Email
        </Button>
        <Button
          type="button"
          size="sm"
          variant={channel === "whatsapp" ? "default" : "outline"}
          className="h-7 text-xs"
          onClick={() => setChannel("whatsapp")}
          disabled={waTemplates.length === 0 && !waWindowActive}
          title={waTemplates.length === 0 && !waWindowActive ? "No approved WhatsApp templates yet" : undefined}
          data-testid="composer-channel-whatsapp"
        >
          WhatsApp
        </Button>
        {!leadStage && (
          <span className="ml-2 text-[11px] text-amber-600 dark:text-amber-400">
            Lead stage unavailable — sending is disabled until JAWIS is reachable.
          </span>
        )}
      </div>

      <div className="mb-2 flex flex-wrap items-center gap-1">
        <Sparkles className="h-3 w-3 text-primary" />
        <Button variant="ghost" size="sm" className="h-6 px-1.5 text-[11px]" onClick={handleAiReply} disabled={aiBusy !== null} data-testid="ai-reply">
          {aiBusy === "reply" ? "…" : "AI Reply"}
        </Button>
        <Button variant="ghost" size="sm" className="h-6 px-1.5 text-[11px]" onClick={handleSummarize} disabled={aiBusy !== null} data-testid="ai-summarize">
          {aiBusy === "summarize" ? "…" : "Summarize conversation"}
        </Button>
        <Button variant="ghost" size="sm" className="h-6 px-1.5 text-[11px]" onClick={handleFollowUp} disabled={aiBusy !== null} data-testid="ai-followup">
          {aiBusy === "followup" ? "…" : "Generate follow-up"}
        </Button>
      </div>

      <div className="rounded-xl border border-border bg-card p-3">
        {channel === "email" ? (
          <div className="space-y-2">
            <Select value={templateId} onValueChange={setTemplateId}>
              <SelectTrigger className="h-8 text-xs" data-testid="composer-email-template">
                <SelectValue placeholder="Custom message" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={CUSTOM}>Custom message</SelectItem>
                {emailTemplates.map((t) => (
                  <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>

            {templateId === CUSTOM ? (
              <>
                <Input
                  placeholder="Subject"
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  className="h-8 text-sm"
                  data-testid="composer-input"
                />
                <Textarea
                  placeholder="Write a message…"
                  rows={2}
                  value={body}
                  onChange={(e) => setBody(e.target.value)}
                  className="resize-none border-0 bg-transparent p-0 text-sm focus-visible:ring-0 focus-visible:ring-offset-0"
                />
                {body.trim() && (
                  <div className="flex flex-wrap items-center gap-1 border-t border-border/60 pt-1.5">
                    <Button variant="ghost" size="sm" className="h-6 gap-1 px-1.5 text-[11px]" onClick={() => handleDraftTransform("rewrite")} disabled={aiBusy !== null} data-testid="ai-rewrite">
                      <Wand2 className="h-3 w-3" /> Rewrite
                    </Button>
                    <Button variant="ghost" size="sm" className="h-6 gap-1 px-1.5 text-[11px]" onClick={() => handleDraftTransform("shorten")} disabled={aiBusy !== null} data-testid="ai-shorten">
                      <Scissors className="h-3 w-3" /> Shorten
                    </Button>
                    <Button variant="ghost" size="sm" className="h-6 gap-1 px-1.5 text-[11px]" onClick={() => handleDraftTransform("professional")} disabled={aiBusy !== null} data-testid="ai-professional">
                      <Briefcase className="h-3 w-3" /> Professional
                    </Button>
                    <Button variant="ghost" size="sm" className="h-6 gap-1 px-1.5 text-[11px]" onClick={() => handleDraftTransform("friendly")} disabled={aiBusy !== null} data-testid="ai-friendly">
                      <SmileyIcon className="h-3 w-3" /> Friendly
                    </Button>
                    <Select value={translateLang} onValueChange={setTranslateLang}>
                      <SelectTrigger className="h-6 w-24 text-[11px]"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        {TRANSLATE_LANGUAGES.map((l) => <SelectItem key={l} value={l} className="text-xs">{l}</SelectItem>)}
                      </SelectContent>
                    </Select>
                    <Button variant="ghost" size="sm" className="h-6 gap-1 px-1.5 text-[11px]" onClick={() => handleDraftTransform("translate", translateLang)} disabled={aiBusy !== null} data-testid="ai-translate">
                      <Languages className="h-3 w-3" /> Translate
                    </Button>
                  </div>
                )}
              </>
            ) : (
              <div className="space-y-1.5">
                {emailVars.length === 0 ? (
                  <p className="text-xs text-muted-foreground">{selectedEmailTemplate?.content}</p>
                ) : (
                  emailVars.map((v) => (
                    <Input
                      key={v}
                      placeholder={`{{${v}}}`}
                      value={variables[v] || ""}
                      onChange={(e) => setVar(v, e.target.value)}
                      className="h-7 text-xs"
                    />
                  ))
                )}
              </div>
            )}
          </div>
        ) : waWindowActive ? (
          // Live Chat mode — the 24h customer-service session window is
          // open (a real inbound reply within the last 24h). Template
          // selector hidden; plain freeform text instead, WhatsApp-Web
          // style Enter-to-send.
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-1 text-[11px] text-muted-foreground">
              <MessageCircleIcon className="h-3 w-3 text-emerald-500" />
              <span>Live chat — customer replied within the last 24 hours.</span>
            </div>
            <div className="mb-1 flex flex-wrap items-center gap-1">
              <Sparkles className="h-3 w-3 text-primary" />
              <Button variant="ghost" size="sm" className="h-6 px-1.5 text-[11px]" onClick={handleWaSuggested} disabled={aiBusy !== null} data-testid="ai-wa-suggested">
                {aiBusy === "wa-suggested" ? "…" : "Suggested"}
              </Button>
              <Button variant="ghost" size="sm" className="h-6 px-1.5 text-[11px]" onClick={() => handleWaTransform("professional")} disabled={aiBusy !== null} data-testid="ai-wa-professional">
                {aiBusy === "professional" ? "…" : "Professional"}
              </Button>
              <Button variant="ghost" size="sm" className="h-6 px-1.5 text-[11px]" onClick={() => handleWaTransform("translate", "Hindi")} disabled={aiBusy !== null} data-testid="ai-wa-hindi">
                {aiBusy === "translate" ? "…" : "Hindi"}
              </Button>
              <Button variant="ghost" size="sm" className="h-6 px-1.5 text-[11px]" onClick={() => handleWaTransform("translate", "English")} disabled={aiBusy !== null} data-testid="ai-wa-english">
                {aiBusy === "translate" ? "…" : "English"}
              </Button>
            </div>
            <Textarea
              placeholder="Type a WhatsApp message… (Enter to send, Shift+Enter for a new line)"
              rows={2}
              value={waFreeText}
              onChange={(e) => setWaFreeText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              className="resize-none border-0 bg-transparent p-0 text-sm focus-visible:ring-0 focus-visible:ring-offset-0"
              data-testid="composer-whatsapp-freetext"
            />
          </div>
        ) : (
          // Locked mode — no reply yet, or the 24h window has expired.
          // Template sending stays enabled; automation is untouched
          // (Journey/Automation Engine sends independently of this UI).
          <div className="space-y-2">
            <div className="flex items-start gap-1.5 rounded-md bg-secondary/50 p-2 text-[11px] text-muted-foreground">
              <Lock className="mt-0.5 h-3 w-3 shrink-0" />
              <span>
                {waWindow?.everReplied
                  ? "The WhatsApp customer service session has expired. Send an approved template to reopen the conversation."
                  : "Waiting for customer reply. Manual WhatsApp messages become available after the customer replies within the 24-hour service window."}
              </span>
            </div>
            <Select value={templateId === CUSTOM ? "" : templateId} onValueChange={setTemplateId}>
              <SelectTrigger className="h-8 text-xs" data-testid="composer-whatsapp-template">
                <SelectValue placeholder="Select an approved template…" />
              </SelectTrigger>
              <SelectContent>
                {waTemplates.map((t) => (
                  <SelectItem key={t.id} value={t.id}>{t.template_name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            {selectedWaTemplate && (
              <div className="space-y-1.5">
                <p className="rounded-md bg-secondary/50 p-2 text-xs text-muted-foreground">{selectedWaTemplate.body}</p>
                {waVars.map((v) => (
                  <Input
                    key={v}
                    placeholder={`{{${v}}}`}
                    value={variables[v] || ""}
                    onChange={(e) => setVar(v, e.target.value)}
                    className="h-7 text-xs"
                    data-testid={`composer-wa-var-${v}`}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        <div className="mt-2 flex items-center justify-between border-t border-border/60 pt-2">
          <div className="flex items-center gap-0.5">
            <Button variant="ghost" size="icon" className="h-7 w-7" disabled title="Attachments not wired to a backend yet">
              <Paperclip className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="icon" className="h-7 w-7" disabled title="Emoji picker not wired yet">
              <Smile className="h-4 w-4" />
            </Button>
          </div>
          <Button size="sm" className="h-7" onClick={handleSend} disabled={!contentReady || sending} data-testid="composer-send">
            <Send className="mr-1 h-3 w-3" /> {sending ? "Sending…" : "Send"}
          </Button>
        </div>
      </div>

      <Dialog open={!!aiResult} onOpenChange={(open) => !open && setAiResult(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{aiResult?.title}</DialogTitle>
          </DialogHeader>
          <p className="whitespace-pre-wrap text-sm text-muted-foreground">{aiResult?.text}</p>
        </DialogContent>
      </Dialog>
    </div>
  );
}

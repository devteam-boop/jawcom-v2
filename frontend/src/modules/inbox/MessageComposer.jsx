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
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Send, Paperclip, Smile, Lock, Sparkles, Wand2, Scissors, Briefcase, Smile as SmileyIcon, Languages } from "lucide-react";
import { templateService } from "@/services/templates";
import { whatsappTemplateService } from "@/services/whatsappTemplates";
import { messageService } from "@/services/messages";
import { aiTextService } from "@/services/aiText";
import { aiAssistantService } from "@/services/aiAssistant";
import { aiSummaryService } from "@/services/aiSummary";
import { useAgentSession } from "@/hooks/useAgentSession";
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
 * Sending requires an agent session (Phase 3, Task 1) — those routes are
 * Bearer-protected (real WhatsApp/email spend if called by an untrusted
 * caller). Clicking Send with no session prompts an inline login
 * (POST /api/auth/login, a shared workspace passcode — see
 * backend/app/core/session_auth.py) rather than embedding any secret in
 * the frontend bundle.
 *
 * WhatsApp always requires an approved template — Meta's Cloud API only
 * accepts template-addressed sends outside an active session, and this
 * backend has no wired path for freeform WhatsApp text (MetaProvider has a
 * send_message() method for it, but no route/integration calls it — wiring
 * that up is a real new send-path, not a thin proxy, so it's stubbed here
 * rather than faked). Email supports both a template and a fully custom
 * subject/body.
 *
 * Attachments/emoji/voice are stubbed (disabled, tooltip'd) — no upload/
 * media backend exists.
 */
export default function MessageComposer({ leadId, leadStage, onSent }) {
  const { token, login } = useAgentSession();
  const [channel, setChannel] = useState("email");
  const [emailTemplates, setEmailTemplates] = useState([]);
  const [waTemplates, setWaTemplates] = useState([]);
  const [templateId, setTemplateId] = useState(CUSTOM);
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [variables, setVariables] = useState({});
  const [sending, setSending] = useState(false);

  const [loginOpen, setLoginOpen] = useState(false);
  const [password, setPassword] = useState("");
  const [loginError, setLoginError] = useState(null);
  const [loggingIn, setLoggingIn] = useState(false);

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

  const contentReady =
    !!leadStage &&
    (channel === "email"
      ? templateId === CUSTOM
        ? subject.trim() && body.trim()
        : true
      : !!selectedWaTemplate && waVars.every((v) => (variables[v] || "").trim()));

  const doSend = async (sessionToken) => {
    setSending(true);
    try {
      if (channel === "email") {
        const payload =
          templateId === CUSTOM
            ? { lead_id: leadId, template_key: null, stage: leadStage, module: "general", variables: { subject, body } }
            : { lead_id: leadId, template_key: templateId, stage: leadStage, module: "general", variables };
        const result = await messageService.sendEmail(payload, sessionToken);
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
      } else {
        const payload = {
          lead_id: leadId,
          template_name: selectedWaTemplate.template_name,
          language: selectedWaTemplate.language,
          stage: leadStage,
          module: "general",
          variables,
        };
        const result = await messageService.sendWhatsapp(payload, sessionToken);
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
    } catch (err) {
      toast.error(err?.body?.detail || err.message || "Send failed");
    } finally {
      setSending(false);
    }
  };

  const handleSend = async () => {
    if (!contentReady || sending) return;
    if (!token) {
      setLoginError(null);
      setLoginOpen(true);
      return;
    }
    await doSend(token);
  };

  const handleLogin = async () => {
    setLoggingIn(true);
    setLoginError(null);
    try {
      const newToken = await login(password);
      setLoginOpen(false);
      setPassword("");
      await doSend(newToken);
    } catch (err) {
      setLoginError(err?.body?.detail || err.message || "Login failed");
    } finally {
      setLoggingIn(false);
    }
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
          disabled={waTemplates.length === 0}
          title={waTemplates.length === 0 ? "No approved WhatsApp templates yet" : undefined}
          data-testid="composer-channel-whatsapp"
        >
          WhatsApp
        </Button>
        {!leadStage && (
          <span className="ml-2 text-[11px] text-amber-600 dark:text-amber-400">
            Lead stage unavailable — sending is disabled until JAWIS is reachable.
          </span>
        )}
        {token && (
          <span className="ml-auto flex items-center gap-1 text-[11px] text-muted-foreground">
            <Lock className="h-3 w-3" /> Signed in
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
        ) : (
          <div className="space-y-2">
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

      <Dialog open={loginOpen} onOpenChange={setLoginOpen}>
        <DialogContent className="sm:max-w-sm">
          <DialogHeader>
            <DialogTitle>Sign in to send</DialogTitle>
            <DialogDescription>
              Manual sends require an agent session. Enter the workspace passcode.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2 py-1">
            <Label htmlFor="agent-password">Passcode</Label>
            <Input
              id="agent-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleLogin()}
              data-testid="agent-login-password"
              autoFocus
            />
            {loginError && <p className="text-xs text-rose-600 dark:text-rose-400">{loginError}</p>}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setLoginOpen(false)}>Cancel</Button>
            <Button onClick={handleLogin} disabled={loggingIn || !password} data-testid="agent-login-submit">
              {loggingIn ? "Signing in…" : "Sign in & Send"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

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

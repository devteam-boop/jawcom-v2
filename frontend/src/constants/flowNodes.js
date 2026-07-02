import {
  Zap,
  Clock,
  GitBranch,
  MessageCircle,
  Mail,
  Bell,
  Timer,
  StopCircle,
} from "lucide-react";

// V1 node types only. No AI. No SMS. No Voice.
export const NODE_TYPES = {
  trigger: { label: "Trigger", icon: Zap, color: "border-indigo-500/40 bg-indigo-500/10 text-indigo-600 dark:text-indigo-400" },
  delay: { label: "Delay", icon: Clock, color: "border-slate-500/40 bg-slate-500/10 text-slate-600 dark:text-slate-400" },
  condition: { label: "Condition", icon: GitBranch, color: "border-amber-500/40 bg-amber-500/10 text-amber-600 dark:text-amber-400" },
  send_whatsapp: { label: "Send WhatsApp", icon: MessageCircle, color: "border-emerald-500/40 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400" },
  send_email: { label: "Send Email", icon: Mail, color: "border-blue-500/40 bg-blue-500/10 text-blue-600 dark:text-blue-400" },
  notification: { label: "Notification", icon: Bell, color: "border-pink-500/40 bg-pink-500/10 text-pink-600 dark:text-pink-400" },
  wait: { label: "Wait", icon: Timer, color: "border-slate-500/40 bg-slate-500/10 text-slate-600 dark:text-slate-400" },
  end: { label: "End", icon: StopCircle, color: "border-rose-500/40 bg-rose-500/10 text-rose-600 dark:text-rose-400" },
};

export const NODE_PALETTE_ORDER = [
  "trigger",
  "delay",
  "condition",
  "send_whatsapp",
  "send_email",
  "notification",
  "wait",
  "end",
];

export const INSTANCE_STATUS_TONE = {
  pending: "neutral",
  running: "info",
  waiting: "warning",
  paused: "warning",
  failed: "danger",
  completed: "success",
  cancelled: "neutral",
};

import { MessageCircle, Mail, Radio } from "lucide-react";
import { cn } from "@/lib/utils";

// Real CommunicationEvent.channel values are lowercase ("whatsapp", "email",
// "system"). Any future channel (e.g. a Meta Cloud API/Resend-specific
// value, or a new channel type entirely) falls back to a generic badge
// instead of rendering nothing — this list is not exhaustive by design.
const CHANNEL_ICON = {
  whatsapp: MessageCircle,
  email: Mail,
};

const CHANNEL_COLOR = {
  whatsapp: "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400",
  email: "bg-blue-500/10 text-blue-700 dark:text-blue-400",
};

export default function ChannelBadge({ channel, className }) {
  const Icon = CHANNEL_ICON[channel] || Radio;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider",
        CHANNEL_COLOR[channel] || "bg-secondary text-secondary-foreground",
        className
      )}
    >
      <Icon className="h-3 w-3" />
      {channel || "unknown"}
    </span>
  );
}

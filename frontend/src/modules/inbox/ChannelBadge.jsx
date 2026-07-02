import { MessageCircle, Mail, Instagram, Facebook, MessageSquare } from "lucide-react";
import { cn } from "@/lib/utils";

const channelIcon = {
  WhatsApp: MessageCircle,
  Email: Mail,
  Instagram: Instagram,
  Facebook: Facebook,
  SMS: MessageSquare,
};

const channelColor = {
  WhatsApp: "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400",
  Email: "bg-blue-500/10 text-blue-700 dark:text-blue-400",
  Instagram: "bg-pink-500/10 text-pink-700 dark:text-pink-400",
  Facebook: "bg-indigo-500/10 text-indigo-700 dark:text-indigo-400",
  SMS: "bg-amber-500/10 text-amber-700 dark:text-amber-400",
};

export default function ChannelBadge({ channel, className }) {
  const Icon = channelIcon[channel] || MessageCircle;
  return (
    <span className={cn("inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider", channelColor[channel] || "bg-secondary", className)}>
      <Icon className="h-3 w-3" />
      {channel}
    </span>
  );
}

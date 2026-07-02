import {
  LayoutDashboard,
  MessagesSquare,
<<<<<<< HEAD
  Workflow,
  Megaphone,
  FileText,
  BarChart3,
=======
  Users,
  Megaphone,
  Zap,
  Workflow,
  FileText,
>>>>>>> 321075ad65aa3df54916ae638505753705e9661b
  BookOpen,
  Sparkles,
  Plug,
  Code,
  Settings as SettingsIcon,
} from "lucide-react";

<<<<<<< HEAD
// Redesigned navigation per architecture review (see ARCHITECTURE.md):
// - "Contacts" removed — JawCom never owns customer data (JAWIS owns it).
// - "Automation" removed as a standalone item — Flow Builder now lives inside
//   each Journey (/journeys/:id/flow).
// - "Journey Monitor" renamed to "Journeys" — it's a management hub, not a
//   passive monitor.
// - "Reports" added — dedicated communication analytics hub.
// - "Conversations" renamed to "Inbox".
export const NAV_ITEMS = [
  { label: "Dashboard", path: "/", icon: LayoutDashboard, testId: "nav-dashboard" },
  { label: "Inbox", path: "/inbox", icon: MessagesSquare, testId: "nav-inbox", badge: 12 },
  { label: "Journeys", path: "/journeys", icon: Workflow, testId: "nav-journeys" },
  { label: "Campaigns", path: "/campaigns", icon: Megaphone, testId: "nav-campaigns" },
  { label: "Templates", path: "/templates", icon: FileText, testId: "nav-templates" },
  { label: "Reports", path: "/reports", icon: BarChart3, testId: "nav-reports" },
=======
export const NAV_ITEMS = [
  { label: "Dashboard", path: "/", icon: LayoutDashboard, testId: "nav-dashboard" },
  { label: "Inbox", path: "/conversations", icon: MessagesSquare, testId: "nav-inbox", badge: 12 },
  { label: "Contacts", path: "/contacts", icon: Users, testId: "nav-contacts" },
  { label: "Campaigns", path: "/campaigns", icon: Megaphone, testId: "nav-campaigns" },
  { label: "Automation", path: "/automation", icon: Zap, testId: "nav-automation" },
  { label: "Journey Monitor", path: "/journeys", icon: Workflow, testId: "nav-journey-monitor" },
  { label: "Templates", path: "/templates", icon: FileText, testId: "nav-templates" },
>>>>>>> 321075ad65aa3df54916ae638505753705e9661b
  { label: "Knowledge", path: "/knowledge", icon: BookOpen, testId: "nav-knowledge" },
  { label: "AI Assistant", path: "/assistant", icon: Sparkles, testId: "nav-assistant" },
  { label: "Integrations", path: "/integrations", icon: Plug, testId: "nav-integrations" },
  { label: "Developers", path: "/developers", icon: Code, testId: "nav-developers" },
  { label: "Settings", path: "/settings", icon: SettingsIcon, testId: "nav-settings" },
];

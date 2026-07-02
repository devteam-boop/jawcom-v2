# JawCom — AI Customer Communication Platform

## Original problem statement
Build a FRONTEND-ONLY React SaaS app called JawCom — an AI Customer Communication Platform inspired by HubSpot CRM + Intercom inbox, kept minimal like Linear. Single-pass, no backend, no auth, no DB. All data hardcoded. Indigo accent on neutral grays, light + dark mode, rounded-xl cards, reusable components. Subsequent expansion: Companies, Automation, Workflow Builder, Templates, Knowledge, Developers, Global Search, AI Memory, Conversation Timeline tab.

## Architecture
- Stack: React (CRA + craco) + Tailwind + shadcn/ui + React Router + recharts + lucide-react.
- Folder structure (drop-in ready for FastAPI backend): `pages/`, `layouts/`, `components/`, `features/`, `hooks/`, `services/`, `constants/`, `dummy-data/`, `theme/`.
- Persistent AppLayout (Sidebar + Header + `<Outlet/>`). All data is read from `src/dummy-data/*`. `src/services/index.js` holds empty placeholder async functions.

## User personas
- Sales / CS rep — Conversations, Follow-ups, Assistant.
- Marketing / growth lead — Campaigns, Journeys, Automation, Reports.
- Workspace admin — Integrations, Settings, team & roles.
- Developer — Developers (keys, webhooks, SDK, REST).

## Core requirements (static)
- 17 routes via persistent layout: `/`, `/conversations`, `/customers`, `/companies`, `/campaigns`, `/journeys`, `/automation`, `/automation/builder`, `/assistant`, `/templates`, `/knowledge`, `/followups`, `/reports`, `/integrations`, `/developers`, `/settings`, `/search`.
- Reusable components used everywhere: `StatCard`, `ChartCard`, `DataTable`, `StatusBadge`, `SearchBar`, `FilterBar`, `PageHeader`, `EmptyState`, `LoadingSkeleton`, `ThemeToggle`.
- Design system locked: single indigo-600 accent, neutral grays, rounded-xl cards, Plus Jakarta Sans + IBM Plex Mono, light + dark.
- Responsive: sidebar collapses on mobile.
- No network calls, no backend, no auth.

## What's been implemented

### Feb 14, 2026 — Initial MVP
- Theme, AppLayout (Sidebar + Header), Dashboard, Conversations, Customers, Campaigns, Journeys, AI Assistant, Follow-ups, Reports, Integrations, Settings.

### Feb 14, 2026 — Enterprise expansion (this pass)
- **Companies** (`/companies`) — 12-row B2B DataTable with right Drawer (Overview, Contacts, Conversations, Campaigns, Journey timeline, Notes, AI Summary).
- **Automation** (`/automation`) — 8 workflow cards + Drawer (Overview, Trigger, Conditions, Actions, History, Settings).
- **Workflow Builder** (`/automation/builder`) — static 3-column visual diagram. Pure CSS + SVG (no react-flow / dnd-kit). 9-node palette, 9 pre-placed nodes connected via curved SVG edges with arrow markers, properties panel with Label / Type / Description / Skip-on-error / Log toggle.
- **Templates** (`/templates`) — 4-tab grid (WhatsApp, Email, SMS, Voice) with 15 template cards, preview snippets, status badges, edit/duplicate actions.
- **Knowledge** (`/knowledge`) — searchable doc library with type filter chips (Website, PDF, FAQ, Pricing, Policies, Brochure, Drive), 10 doc cards showing Status, Embedding, AI Ready badge, Chunk Count + 4 summary tiles.
- **Developers** (`/developers`) — 6-tab page: API Keys, Webhooks, REST API (with cURL code blocks), OAuth Apps, Event Logs (live-tail style), SDKs (JS/Python/Go/Ruby).
- **Global Search** (`/search`) — header search now navigates to a dedicated search page with 6 tabs (All / Conversations / People / Companies / Campaigns / Knowledge) that cross-searches all dummy data.
- **Header notification center** — expanded to a rich panel with colored dot statuses, secondary previews, mark-all-read.
- **AI Memory** — new section inside `/assistant` with 6 long-term memory entries + Knowledge usage card.
- **Conversation Timeline tab** — new "Conv." tab inside the Customers drawer showing the customer's last few threads with channel, preview and status.
- **Sidebar** — appended Companies, Automation, Templates, Knowledge, Developers as new nav entries (existing icons + active-state style preserved).

## Prioritized backlog
- P0: None — full enterprise UI shell delivered per spec.
- P1: Wire `services/index.js` to real backend; auth (JWT or Emergent Google); live inbox via websockets.
- P2: Real drag-and-drop in `AutomationBuilder` (requires adding react-flow / dnd-kit which was explicitly forbidden this pass); RBAC enforcement; mobile-first composer.

## Next tasks
- Backend wiring through `src/services/`.
- Optional: CRA → Vite + TS migration (requires supervisor config change).
- Optional: enable real drag-and-drop in the workflow builder behind a feature flag.

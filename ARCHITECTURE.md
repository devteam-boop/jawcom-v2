# JawCom Architecture — Principal Architect Review

> ⚠️ **ARCHIVED — PROPOSAL, NOT CURRENT ARCHITECTURE**
>
> This document is a redesign **proposal** from 2026-07-02. It was never fully
> implemented: the frontend nav still uses the pre-proposal structure
> (`/conversations`, standalone `/contacts`, `/automation`), and the backend
> that was built afterward (19 completed sprints — execution engine, executor
> framework, integrations, JAWIS live integration) diverged from this doc's
> MongoDB/collection-based data model in favor of PostgreSQL + SQLAlchemy.
>
> **Current source of truth:** [`docs/architecture.md`](docs/architecture.md)
> (implementation) and [`docs/AI_CONTEXT.md`](docs/AI_CONTEXT.md) (quick
> reference). See also `docs/roadmap.md`, `docs/module_dependencies.md`,
> `docs/decisions.md`, `docs/KNOWN_ISSUES.md`.
>
> This file is kept for its **Inbox / Timeline / Campaign / Channel
> abstraction design ideas** (sections 11-13), which remain unimplemented and
> may still be useful reference material for that future work. Do not treat
> any other section (nav structure, data model, implementation order) as
> reflecting the current codebase.

> **Author**: Principal Architect Review
> **Date**: 2026-07-02
> **Context**: Redesign of Communication Journey architecture for JawCom (Communication OS) integrated with JAWIS (Business OS).

---

## Table of Contents

1. [Domain Boundaries](#1-domain-boundaries)
2. [Navigation Redesign](#2-navigation-redesign)
3. [Module Organization](#3-module-organization)
4. [Router Architecture](#4-router-architecture)
5. [Stage Mapping Redesign](#5-stage-mapping-redesign)
6. [Journey Page Structure](#6-journey-page-structure)
7. [Flow Builder](#7-flow-builder)
8. [Flow Nodes](#8-flow-nodes)
9. [Templates](#9-templates)
10. [Running Instance State Machine](#10-running-instance-state-machine)
11. [Campaigns](#11-campaigns)
12. [Inbox & JAWIS Context](#12-inbox--jawis-context)
13. [Channel Abstraction Layer](#13-channel-abstraction-layer)
14. [Data Flow Architecture](#14-data-flow-architecture)
15. [Data Model](#15-data-model)
16. [What to Remove for V1](#16-what-to-remove-for-v1)
17. [What to Merge](#17-what-to-merge)
18. [What Is Missing From the Spec](#18-what-is-missing-from-the-spec)
19. [Scalability Rules](#19-scalability-rules)
20. [Implementation Order](#20-implementation-order)

---

## 1. Domain Boundaries

```
JAWIS (Business OS)                  JawCom (Communication OS)
─────────────────────                ───────────────────────────
Owns:                                Owns:
  • Leads                              • WhatsApp communication
  • Companies                          • Email communication
  • Customers                          • Templates (reusable assets)
  • Lead Stages                        • Journeys (stage → flow mapping)
  • Requirements                       • Flow definitions
  • Tasks                              • Running journey instances
  • Sales Pipeline                     • Campaigns (one-to-many broadcasts)
  • User roles/permissions             • Inbox (conversation threads)
                                       • Communication analytics
                                       • Channel integrations

                              NEVER owns customer data
                              NEVER edits lead stages
                              ONLY reacts to JAWIS business events
```

---

## 2. Navigation Redesign

### Current (problematic)

```
Dashboard     /
Inbox         /conversations
Contacts      /contacts          ← JawCom should NOT own contacts
Campaigns     /campaigns
Automation    /automation        ← Separate from Journeys — WRONG
Journey Mon.  /journeys          ← "Monitor" implies passive, not management
Templates     /templates
Knowledge     /knowledge
AI Assistant  /assistant
Integrations  /integrations
Developers    /developers
Settings      /settings
```

### Proposed

```
LEFT SIDEBAR:
┌───────────────────────────────────┐
│  JawCom  · AI Communication       │
├───────────────────────────────────┤
│  Dashboard          /             │
│  Inbox              /inbox        │   ← renamed from /conversations
│  Journeys           /journeys     │   ← renamed + hub for all journey ops
│  Campaigns          /campaigns    │
│  Templates          /templates    │
│  Reports            /reports      │   ← NEW — dedicated analytics hub
│  Knowledge          /knowledge    │   ← deferred post-V1
│  AI Assistant       /assistant    │   ← deferred post-V1
├╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┤
│  Integrations       /integrations │
│  Developers         /developers   │
│  Settings           /settings     │
└───────────────────────────────────┘
```

### Changes summary

| Item | Action | Rationale |
|------|--------|-----------|
| Contacts | **REMOVED** | JawCom does not own customer data |
| Automation | **REMOVED** | Merged into Journeys — Flow Builder lives inside Journey |
| Journey Monitor | **RENAMED → Journeys** | It is a management hub, not a monitor |
| Reports | **ADDED** | Communication analytics need a dedicated section |
| Conversations | **RENAMED → Inbox** | Standard terminology |
| Knowledge | **KEPT but deferred** | Not needed for WhatsApp/Email V1 |
| AI Assistant | **KEPT but deferred** | No AI nodes in flows; separate product concern |

---

## 3. Module Organization

```
frontend/src/
├── pages/                        # Route-level entry points (thin — delegates to modules)
│   ├── Dashboard.jsx
│   ├── Inbox.jsx
│   ├── Journeys.jsx              # /journeys — list + stage mapping
│   ├── JourneyDetail.jsx         # /journeys/:id — 4-section layout with nested routes
│   ├── Campaigns.jsx
│   ├── Templates.jsx
│   ├── Reports.jsx
│   ├── Knowledge.jsx             # deferred
│   ├── Assistant.jsx             # deferred
│   ├── Integrations.jsx
│   ├── Developers.jsx
│   └── Settings.jsx
│
├── modules/                      # Feature modules (co-located: components + hooks + utils)
│   ├── inbox/
│   │   ├── ConversationList.jsx
│   │   ├── ConversationThread.jsx
│   │   ├── MessageComposer.jsx
│   │   ├── JawisContextPanel.jsx     ← READ-ONLY customer data from JAWIS API
│   │   ├── ChannelBadge.jsx
│   │   └── hooks/useConversations.js
│   │
│   ├── journeys/
│   │   ├── JourneyList.jsx
│   │   ├── StageMapping.jsx
│   │   ├── JourneyDashboard.jsx      ← KPI cards + recent instances
│   │   ├── RunningInstances.jsx
│   │   ├── JourneySettings.jsx
│   │   ├── FlowBuilder/
│   │   │   ├── FlowCanvas.jsx
│   │   │   ├── NodePalette.jsx
│   │   │   ├── PropertiesPanel.jsx
│   │   │   ├── FlowToolbar.jsx
│   │   │   └── nodes/
│   │   │       ├── TriggerNode.jsx
│   │   │       ├── DelayNode.jsx
│   │   │       ├── ConditionNode.jsx
│   │   │       ├── SendWhatsAppNode.jsx
│   │   │       ├── SendEmailNode.jsx
│   │   │       ├── NotificationNode.jsx
│   │   │       ├── WaitNode.jsx
│   │   │       └── EndNode.jsx
│   │   └── hooks/
│   │       ├── useJourneys.js
│   │       ├── useFlowBuilder.js
│   │       └── useRunningInstances.js
│   │
│   ├── campaigns/
│   │   ├── CampaignList.jsx
│   │   ├── CampaignWizard.jsx
│   │   └── hooks/useCampaigns.js
│   │
│   ├── templates/
│   │   ├── TemplateList.jsx
│   │   ├── TemplatePreview.jsx
│   │   └── hooks/useTemplates.js
│   │
│   └── reports/
│       ├── DeliveryReport.jsx
│       ├── JourneyAnalytics.jsx
│       ├── CampaignAnalytics.jsx
│       └── hooks/useReports.js
│
├── components/                   # Shared/generic components
│   ├── ui/                       # shadcn/Radix primitives (keep as-is)
│   ├── DataTable.jsx
│   ├── PageHeader.jsx
│   ├── StatCard.jsx
│   ├── StatusBadge.jsx
│   ├── EmptyState.jsx
│   ├── LoadingSkeleton.jsx
│   ├── FilterBar.jsx
│   └── SearchBar.jsx
│
├── services/                     # API layer (replaces dummy-data imports)
│   ├── index.js                  # Service registry
│   ├── journeys.js
│   ├── inbox.js
│   ├── campaigns.js
│   ├── templates.js
│   ├── reports.js
│   ├── integrations.js
│   └── jawis.js                  # READ-ONLY JAWIS sync client
│
├── hooks/                        # Global hooks
│   ├── useTheme.js
│   └── useToast.js
│
├── layouts/
│   └── AppLayout.jsx
│
├── constants/
│   ├── nav.js
│   ├── flowNodes.js              # Node type definitions
│   └── channels.js               # WhatsApp | Email channel configs
│
├── lib/
│   └── utils.js
│
├── App.js
├── App.css
└── index.js
```

### Key architectural rules for modules

1. Each module owns its components, hooks, and utils — no cross-module imports of internal files
2. Modules communicate through the services layer, not through direct imports
3. Pages are thin — one page file per route, delegates to module components
4. No module imports from `dummy-data/` — that directory is deleted when services are wired

---

## 4. Router Architecture

```
<Routes>
  <Route element={<AppLayout />}>
    <Route path="/"                       element={<Dashboard />} />
    <Route path="/inbox"                  element={<Inbox />} />
    <Route path="/journeys"               element={<Journeys />} />
    <Route path="/journeys/:id"           element={<JourneyDetail />}>
      <Route index                         element={<Navigate to="dashboard" replace />} />
      <Route path="dashboard"              element={<JourneyDashboard />} />
      <Route path="flow"                   element={<FlowBuilder />} />
      <Route path="running"                element={<RunningInstances />} />
      <Route path="settings"               element={<JourneySettings />} />
    </Route>
    <Route path="/campaigns"             element={<Campaigns />} />
    <Route path="/templates"             element={<Templates />} />
    <Route path="/reports"               element={<Reports />} />
    <Route path="/integrations"          element={<Integrations />} />
    <Route path="/developers"            element={<Developers />} />
    <Route path="/settings"              element={<Settings />} />
    <Route path="*"                      element={<Navigate to="/" replace />} />
  </Route>
</Routes>
```

Journey detail uses nested routes so the sidebar and journey header persist while switching between Dashboard / Flow / Running / Settings tabs.

---

## 5. Stage Mapping Redesign

### Problem with original spec

5 fields (Automation Enabled, Auto Start, Auto Stop, Manual Override, Priority) create ambiguity:
- Auto Start + Manual Override are contradictory
- Auto Stop is unclear (stop when lead enters or exits?)
- Priority is meaningless without a conflict resolution strategy

### Simplified model

```
StageMapping:
  stage_key:    string     // e.g. "qualified", "won" — plain string, NOT a FK to JAWIS
  journey_id:   string     // which journey to trigger
  trigger:      "enter" | "exit" | "reenter"
  mode:         "automatic" | "manual"    // manual = operator must confirm
  enabled:      boolean
```

- `stage_key` is a plain string — JAWIS can add/edit stages without JawCom code changes
- No `priority` — if two mappings match, the most recently updated wins (or show conflict in UI)
- `mode: "manual"` replaces Manual Override
- `trigger: "exit"` replaces Auto Stop

### Example mappings

| JAWIS Stage | Trigger | Mode | Journey |
|-------------|---------|------|---------|
| `qualified` | enter | automatic | Lead Qualification |
| `demand-follow-up` | enter | automatic | Demand Journey |
| `won` | enter | automatic | Customer Success |
| `lost` | enter | manual | Win Back Journey |
| `unqualified` | exit | automatic | (stop any running journey) |

---

## 6. Journey Page Structure

### Problem with original spec

7 tabs (Overview, Flow, Templates, Running Leads, Campaigns, Analytics, Settings) is too many. Campaigns do not belong inside a Journey. Templates inside a Journey should only show references.

### Redesigned — 4 sections

```
JourneyDetail (/journeys/:id)
├── Dashboard       KPI cards + running instance count + recent activity + health
├── Flow            Flow Builder (canvas + palette + properties + toolbar)
├── Running         Live instances table with operator controls
└── Settings        Stage mapping + retry policy + business hours + defaults
```

**Removed from Journey:**
- **Templates** — available globally at `/templates`; Journey only references them via Flow nodes
- **Campaigns** — standalone module at `/campaigns`
- **Analytics** — key metrics rolled into Dashboard; full analytics at `/reports`

### Journey list view

```
Journeys (/journeys)
┌─────────────────────────────────────────────────────────────────┐
│  [Search]  [Filter by status]  [+ Create Journey]              │
├─────────────────────────────────────────────────────────────────┤
│  Journey Name    │ Status  │ Stage Mapping  │ Running │ Health │
│──────────────────┼─────────┼────────────────┼─────────┼────────┤
│ Lead Qualific.   │ Active  │ qualified      │ 142     │ 98%    │
│ Demand Journey   │ Active  │ demand-followup│ 53      │ 95%    │
│ Customer Success │ Draft   │ won            │ 0       │ —      │
│ Win Back         │ Paused  │ lost           │ 12      │ 87%    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Flow Builder

### Ownership

Flow Builder belongs **inside** a Journey. It is NOT an independent product. There is no standalone `/automation` page.

### V1 simplicity

- One active flow per Journey
- Flow is stored as a JSON blob (`flow_definition`)
- A `version` integer auto-increments on each save
- No draft/published split — the saved flow IS the active flow
- No V1/V2 branching — add version management post-V1

### Editor layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  Journey: Lead Qualification  │  [Save] [Publish] [Validate]       │
├──────────┬───────────────────────────────────────────┬──────────────┤
│ Palette  │          Canvas                           │ Properties   │
│          │                                           │              │
│ Trigger  │    [Trigger] → [Delay] → [Condition]     │ Type: Delay  │
│ Delay    │                    │                      │ Duration:    │
│ Cond.    │               Yes  ↓  No                  │ [24 hours]   │
│ Send WA  │              [Send] [Notify]              │              │
│ Send EM  │                 ↓                         │              │
│ Notify   │              [End]                        │              │
│ Wait     │                                           │              │
│ End      │                                           │              │
└──────────┴───────────────────────────────────────────┴──────────────┘
```

### Key UX decisions

- Drag nodes from palette to canvas
- Connect nodes by dragging from output port to input port
- Click a node to open properties panel
- Canvas uses a library like React Flow (reactflow) — don't build SVG from scratch
- Condition node shows editable expression builder (e.g., `lead.stage == "qualified"`)

---

## 8. Flow Nodes

### V1 node types

| Node | Purpose | Configuration |
|------|---------|---------------|
| **Trigger** | Entry point — fired by Stage Mapping or manual start | None (auto-wired to journey trigger) |
| **Delay** | Wait for a duration before proceeding | `duration: number`, `unit: "minutes" \| "hours" \| "days"` |
| **Condition** | Branch based on lead attribute | `field: string`, `operator: "==" \| "!=" \| "in"`, `value: any` |
| **Send WhatsApp** | Send a Meta-approved template | `template_id: string`, `variable_mapping: Record<string, string>` |
| **Send Email** | Send an internal-approved email | `template_id: string`, `variable_mapping: Record<string, string>` |
| **Notification** | Internal alert to workspace operators | `channel: "in-app" \| "email"`, `message: string` |
| **Wait** | Pause until a specific datetime or external event | `type: "until_time" \| "until_event"`, `value: string` |
| **End** | Terminal node — marks instance as completed | None |

### Node execution interface (backend)

Every node implements:

```python
class FlowNode:
    type: str
    config: dict

    async def execute(context: ExecutionContext) -> NodeResult:
        """
        context contains:
          - lead_id, journey_id, instance_id, flow_version
          - jawis_client (read-only)
          - channel_clients (whatsapp, email)
          - logger
        Returns NodeResult(next_node_id, status, output_data)
        """
        ...
```

This interface pattern allows future node types (SMS, Voice, AI) to be added without modifying the engine.

---

## 9. Templates

### Principles

- Templates are **reusable assets** shared across Journeys and Campaigns
- Flow NEVER stores message text inline — only `template_id` + `variable_mapping`
- WhatsApp templates must be Meta-approved before they can be used
- Email templates are approved internally

### Template model

```
Template:
  id:              string
  channel:         "whatsapp" | "email"
  name:            string
  category:        string
  status:          "draft" | "pending_review" | "approved" | "rejected" | "archived"
  body:            string            // template content with {{variable}} placeholders
  variables:       string[]          // extracted from body
  meta_template_id: string?          // for WhatsApp — Meta's template ID
  version:         integer
  created_at:      datetime
  updated_at:      datetime
```

### Template usage tracking

```
TemplateUsage:
  template_id:     string
  used_by_type:    "journey" | "campaign" | "flow_version"
  used_by_id:      string
  node_id:         string?           // which flow node references this template
```

UI shows "Used by 3 Journeys, 2 Campaigns, 5 Flow Versions" with drill-down links.

### Variable mapping at send time

Flow nodes store:

```json
{
  "template_id": "welcome_whatsapp",
  "variable_mapping": {
    "customer_name": "{{lead.name}}",
    "company_name": "{{lead.company.name}}",
    "appointment_date": "{{lead.next_action_date}}"
  }
}
```

The source expressions (`{{lead.*}}`) reference JAWIS fields resolved at execution time.

---

## 10. Running Instance State Machine

### State enum

```
RunningInstance.status:
  pending      → mapped but not yet started
  running      → actively executing flow
  waiting      → paused on a Wait node (awaiting time or event)
  paused       → operator paused
  failed       → node execution error (will retry based on policy)
  completed    → reached End node
  cancelled    → operator cancelled
```

### State transitions

```
pending ──► running ──► waiting ──► running ──► completed
                │                        │
                ├──► paused ─────────────┤
                │        │               │
                │        └──► running    │
                │                        │
                └──► failed ─────────────┤
                         │               │
                         └──► running    │
                              (retry)    │
                                         └──► cancelled
```

### Instance data model

```
RunningInstance:
  id:               string
  lead_id:          string
  journey_id:       string
  flow_version:     integer
  current_node_id:  string
  status:           RunningInstanceStatus
  node_states:      Record<string, NodeState>   // per-node execution state
  context:          {                           // mutable execution context
    variables:      Record<string, any>
    jawis_data:     Record<string, any>          // cached JAWIS lead fields
  }
  started_at:       datetime
  next_execution:   datetime?                    // for Delay/Wait nodes
  last_execution:   datetime?
  completed_at:     datetime?
  events:           InstanceEvent[]              // immutable audit log
```

### InstanceEvent

```
InstanceEvent:
  timestamp:        datetime
  type:             "started" | "node_entered" | "node_completed"
                    | "node_failed" | "paused" | "resumed"
                    | "cancelled" | "completed"
  node_id:          string?
  message:          string
  metadata:         Record<string, any>?
```

---

## 11. Campaigns

### Relationship to Journeys

- **Campaigns are one-to-many broadcasts** (send template to N leads at once)
- **Journeys are one-to-one automation** (per-lead state machine)
- They share Templates but have independent execution models
- Campaigns do NOT belong inside a Journey view

### Campaign model

```
Campaign:
  id:               string
  name:             string
  channel:          "whatsapp" | "email"
  template_id:      string
  variable_mapping: Record<string, string>
  audience_filter:  object           // criteria to select leads (resolved against JAWIS)
  schedule_type:    "now" | "scheduled" | "recurring"
  scheduled_at:     datetime?
  recurring_cron:   string?
  status:           "draft" | "scheduled" | "running" | "completed" | "paused"
  sent_count:       integer
  delivered_count:  integer
  read_count:       integer
  reply_count:      integer
  created_at:       datetime
```

---

## 12. Inbox & JAWIS Context

### Layout

```
┌──────────────────────────────────────┬──────────────────────────────┐
│                                      │  JAWIS Context Panel        │
│     Conversation Thread              │  (READ ONLY)                │
│                                      │                              │
│  ┌────────────────────────────────┐  │  Lead: Sarah Chen           │
│  │ Agent: Hi Sarah, your demo... │  │  Company: Acme Inc          │
│  ├────────────────────────────────┤  │  Stage: Qualified           │
│  │ Customer: Thanks for...       │  │  Owner: Raj K.              │
│  ├────────────────────────────────┤  ├──────────────────────────────┤
│  │ Agent: Great, I've booked...  │  │  Current Journey:            │
│  └────────────────────────────────┘  │  Lead Qualification         │
│                                      │  Status: Running            │
│  ┌────────────────────────────────┐  │  ── Trigger ✓ (entered)     │
│  │ [Type a message...] [Send]     │  │  ── Delay ✓ (24h wait)      │
│  └────────────────────────────────┘  │  ── Send WhatsApp ⏳ (queued)│
│                                      ├──────────────────────────────┤
│                                      │  Templates Used:             │
│                                      │  • welcome_whatsapp (Sent)   │
│                                      │  Campaign History:           │
│                                      │  • Q4 Promo (Delivered)      │
│                                      ├──────────────────────────────┤
│                                      │  [Manual Sync] Last: 2m ago │
└──────────────────────────────────────┴──────────────────────────────┘
```

### JAWIS sync pattern

- On conversation open, fetch lead/company data from JAWIS API
- Cache for 5 minutes (stale-while-revalidate)
- "Manual Sync" button forces refresh
- JAWIS pushes real-time updates via webhook (optional, post-V1)

### What JawCom stores vs what it fetches

| Data | Source | Stored in JawCom? |
|------|--------|--------------------|
| Message history | JawCom | Yes — own communication data |
| Conversation state | JawCom | Yes — assigned agent, status |
| Template send records | JawCom | Yes — delivery receipts |
| Lead name | JAWIS | No — fetched at render time |
| Company name | JAWIS | No — fetched at render time |
| Lead stage | JAWIS | No — fetched at render time |
| Lead owner | JAWIS | No — cached temporarily |

---

## 13. Channel Abstraction Layer

### Interface

```python
class Channel:
    channel_type: str          # "whatsapp" | "email"

    async def send(
        self,
        template_ref: str,        # WhatsApp: Meta template ID; Email: internal template ID
        variables: dict,          # resolved variable values
        recipient: Recipient,     # {identifier: string, channel_specific: dict}
    ) -> SendResult:
        """Returns message_id and initial status"""
        ...

    async def get_status(
        self,
        message_id: str,
    ) -> MessageStatus:
        """Returns current delivery status"""
        ...

    async def handle_webhook(
        self,
        payload: dict,
    ) -> ChannelEvent:
        """Normalizes incoming webhook to standard event format"""
        ...
```

### V1 implementations

| Channel | Provider | Template source | Approval |
|---------|----------|----------------|----------|
| WhatsApp | Meta Cloud API | Meta-hosted templates | Must be Meta-approved |
| Email | SMTP or Gmail API | JawCom-hosted templates | Internal approval |

### Recipient format

```json
{
  "whatsapp": { "phone_number": "+1234567890" },
  "email": { "address": "sarah@acme.com" }
}
```

### Future channels

Adding a new channel = implement the `Channel` interface + register in channel registry. No changes to Flow Builder, Journey engine, or Template system.

---

## 14. Data Flow Architecture

```
JAWIS                              JawCom
─────                              ──────

Lead Stage Changed
       │
       ▼
Webhook / API call ──────────► Stage Mapping
                                   │
                                   ▼
                            Journey Selected
                                   │
                                   ▼
                         Running Instance Created
                                   │
                                   ▼
                          Flow Execution Engine
                            │              │
                            ▼              ▼
                      Send Node        Condition Node
                            │              │
                            ▼              ▼
                      Channel API      JAWIS API (read)
                      (WhatsApp)       (lead field check)
                            │
                            ▼
                      Message Sent
                            │
                            ▼
                      Webhook Received
                      (delivery/read/reply)
                            │
                            ▼
                      Running Instance
                      State Updated
                            │
                            ▼
                      If End node → completed
                      If next node → continue
```

### Event flow for inbound messages

```
Inbound WhatsApp message
       │
       ▼
WhatsApp Webhook ──► JawCom API
       │                  │
       │                  ▼
       │           Find or create Conversation
       │                  │
       │                  ▼
       │           Store message in thread
       │                  │
       │                  ▼
       │           Update Running Instance
       │           (if Wait node awaiting reply)
       │
       ▼
Notification to workspace operators
```

---

## 15. Data Model

### Collections (MongoDB)

```
collections/
├── stage_mappings          // Stage → Journey mapping
├── journeys                // Journey definitions
├── flow_definitions        // Flow JSON (one per journey, versioned)
├── templates               // Reusable templates
├── template_usages         // Tracking which journeys/campaigns use which templates
├── running_instances       // Active journey instances per lead
├── instance_events         // Immutable audit log for every instance state change
├── conversations           // Inbox conversation threads
├── messages                // Individual messages within conversations
├── campaigns               // Broadcast campaigns
├── campaign_recipients     // Per-recipient campaign delivery status
├── channels                // Channel connection configs (WhatsApp, Email)
├── workspaces              // Multi-tenant workspace config
└── users                   // Workspace users and roles
```

### Key indexes

| Collection | Index | Reason |
|------------|-------|--------|
| `stage_mappings` | `{stage_key: 1, enabled: 1}` | Fast lookup on JAWIS stage change |
| `running_instances` | `{lead_id: 1, status: 1}` | Find active instance for a lead |
| `running_instances` | `{next_execution: 1, status: 1}` | Find instances due for execution |
| `conversations` | `{lead_id: 1}` | Find conversation by lead |
| `messages` | `{conversation_id: 1, created_at: -1}` | Thread view |
| `templates` | `{channel: 1, status: 1}` | Filter available templates |

---

## 16. What to Remove for V1

| Feature | Reason |
|---------|--------|
| Knowledge base | Not needed for WhatsApp/Email V1. Add post-V1 with RAG. |
| AI Assistant | No AI nodes in flows. AI chat is a separate product concern. |
| Voice templates | Out of scope for V1. |
| SMS templates | Out of scope for V1. |
| Contacts page | JawCom does not own customer data. Remove from nav and routes. |
| Automation page | Merged into Journey Flow Builder. |
| AutomationBuilder page | Duplicate of Automation. |
| Developers SDK docs | Keep API keys + webhooks only. Remove SDK examples and OAuth apps. |
| Flow versioning (V1/V2) | V1 = one active flow per journey. Simple version integer. |

---

## 17. What to Merge

| Current | Merged Into | Rationale |
|---------|-------------|-----------|
| Automation page | Journey Flow Builder | Flow builder belongs to a specific journey |
| AutomationBuilder page | (deleted) | Duplicate of Automation page — no unique purpose |
| Journey Monitor page | Journeys list | Same domain; "Monitor" implies passive viewing |

---

## 18. What Is Missing From the Spec

| Gap | Recommendation |
|-----|---------------|
| Retry policy | Add to Journey Settings: `max_retries`, `backoff_seconds`, `dead_letter_action` (skip / pause / notify) |
| Business hours | Add to Journey Settings: `timezone`, `working_days`, `working_hours`. Delay/Wait nodes respect these. If a send is scheduled outside hours, queue until next working period. |
| Rate limiting | Per-channel rate limits. WhatsApp: 250 messages/24h per template. Email: per SMTP provider limits. Add to Channel config. |
| Event log | Every flow execution step produces an immutable `InstanceEvent`. Exposed in Running Instance detail view. |
| Bulk start | Allow operator to manually add a list of leads to a journey (not just stage-change triggered). Useful for backfills. |
| Condition evaluator | Conditions must evaluate JAWIS lead fields + JawCom communication history (e.g., "has been sent template X in last 7 days"). |
| Flow validation | Before publishing, validate: all paths reach End, no orphaned nodes, all template refs exist, all variable mappings resolve. |
| Manual node skip | Operator should be able to skip a node on a running instance (e.g., skip Delay for a VIP lead). |
| Inject message | Operator should be able to inject a manual message into a running instance's timeline. |

---

## 19. Scalability Rules

### Do NOT duplicate CRM

- Never store lead name, company, stage, owner, or pipeline data in JawCom
- Always fetch from JAWIS at read time (with short-lived cache)
- JAWIS is the source of truth for all customer data

### Do NOT duplicate customer tables

- No `customers` collection in JawCom
- No `companies` collection in JawCom
- Lead references use JAWIS `lead_id` — opaque string identifier

### Do NOT duplicate companies

- No company CRUD in JawCom
- Company context comes from JAWIS API
- If needed for performance, cache in JawCom with explicit TTL and invalidation webhook

### Scale horizontally

- Running Instances are isolated per-lead — no cross-lead state
- Flow execution is stateless — all state lives in the instance record
- Scheduler picks up due instances by querying `next_execution` index
- Workers can be scaled independently with no data contention

### Multi-tenant isolation

- Every document has a `workspace_id` field
- All queries filter by `workspace_id`
- Indexes include `workspace_id` as the first field

---

## 20. Implementation Order

### Phase 1 — Foundation

1. Define API contracts for every module (OpenAPI spec)
2. Build JAWIS sync client (read-only API + webhook receiver)
3. Build Stage Mapping CRUD
4. Build Journey CRUD
5. Build Flow Definition storage (JSON blob)

### Phase 2 — Flow Builder

6. Build Flow Canvas (React Flow integration)
7. Build node palette and drag-drop
8. Build properties panel per node type
9. Build flow validation (no orphan nodes, all paths reach End)
10. Delete old Automation and AutomationBuilder pages

### Phase 3 — Flow Execution

11. Build Running Instance state machine
12. Build Flow Execution Engine (graph walker)
13. Build node executors (Delay, Condition, Notification, End)
14. Build WhatsApp channel (Meta Cloud API)
15. Build Email channel (SMTP / Gmail API)
16. Build Send WhatsApp + Send Email node executors
17. Build Wait node executor (time-based + event-based)

### Phase 4 — Inbox

18. Build Conversation store
19. Build JAWIS Context Panel (read-only lead data)
20. Build message composer (send reply)
21. Build inbound webhook handlers (WhatsApp + Email)

### Phase 5 — Campaigns

22. Build Campaign CRUD
23. Build Campaign Wizard (audience selection from JAWIS, template selection)
24. Build Campaign execution engine (batch send)
25. Build delivery/read/reply tracking

### Phase 6 — Reports

26. Build Delivery Report (sent, delivered, read, replied by channel)
27. Build Journey Success Report (completion rate, avg duration, failure points)
28. Build Campaign Success Report (delivery funnel, engagement rate)
29. Build Automation Success Report (node execution stats, retry rates)

### Phase 7 — Hardening

30. Retry policy engine
31. Business hours enforcement
32. Rate limiting
33. RBAC (workspace roles, journey-level permissions)
34. Testing (unit + integration + E2E)
35. Deployment configs (Docker, CI/CD, env management)

---

*End of architecture document.*

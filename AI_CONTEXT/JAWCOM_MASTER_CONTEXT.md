# JAWCOM MASTER CONTEXT

> **Single source of truth for the JawCom project.**
> Read this document before any development task. Update when architecture changes.

---

## 1. Project Overview

### Purpose
JawCom is a Communication OS — an AI-powered customer communication platform that automates outbound messaging (WhatsApp, Email) triggered by business events from JAWIS (Business OS). It provides inbox management, journey-based automation, template management, campaign broadcasting, and communication analytics.

### Vision
To become the standard Communication OS that sits alongside any Business OS, decoupling communication logic from CRM logic so businesses can automate customer engagement without being locked into a single CRM.

### Product Positioning
- Inspired by HubSpot CRM + Intercom inbox, kept minimal like Linear.
- Sits alongside JAWIS (Business OS) as a dedicated Communication OS.
- Targets mid-market B2B companies that need automated WhatsApp/Email outreach triggered by sales pipeline events.
- NOT a CRM. NOT a replacement for JAWIS.

### Non Goals
- Building a CRM or owning customer data.
- Replacing JAWIS or any business OS.
- Building a full ERP solution.
- Voice/SMS channels (post-V1).
- AI-powered flow nodes (post-V1).
- Knowledge base / RAG (post-V1).

### Current Version
v0.1.0 — Frontend prototype with dummy data. Backend scaffold only.

### Development Status
- **Frontend static UI**: ~70% complete (all pages, components, routing, theme)
- **Frontend API wiring**: ~10% complete (service layer defined, not connected)
- **Backend product APIs**: ~5% complete (only status-check scaffold exists)
- **Database domain model**: ~5% complete
- **Auth/Security**: 0% complete
- **Integrations (WhatsApp/Email)**: 0% complete
- **Overall product**: ~28% complete

---

## 2. Product Architecture

### JAWIS (Business OS)
- Owns all customer/business data: Leads, Companies, Customers, Lead Stages, Requirements, Tasks, Sales Pipeline, User Roles/Permissions.
- Emits business events when pipeline state changes.
- Exposes read-only APIs for JawCom to fetch customer context.
- Receives webhook notifications from JawCom for message delivery/read events.

### JawCom (Communication OS)
- Owns all communication artifacts: Templates, Flows, Journeys, Campaigns, Inbox conversations, Messages, Channel integrations, Communication analytics.
- NEVER stores customer data. NEVER owns CRM entities. NEVER edits lead stages.
- Fetches customer context from JAWIS at render time (short-lived cache).
- Reacts to JAWIS business events (lead stage changes) to trigger journeys.

### How they communicate
```
JAWIS → Webhook/API → JawCom: Lead Stage Changed → Stage Mapping → Journey Triggered
JawCom → API (read-only) → JAWIS: Fetch lead/company context for Inbox panel
JawCom → Channel API → WhatsApp/Email: Send messages
Channel → Webhook → JawCom: Delivery receipts, inbound messages
```

### Ownership boundaries
| Owned by JAWIS | Owned by JawCom |
|---|---|
| Leads | Templates |
| Companies | Journeys (Stage → Flow mapping) |
| Customers | Flow Definitions |
| Lead Stages | Running Instances |
| Requirements/Tasks | Campaigns |
| Sales Pipeline | Inbox/Conversations |
| User Roles/Permissions | Messages/Threads |
| | Channel Integrations |
| | Communication Analytics |

### Business Events
- `lead.created` — New lead entered pipeline
- `lead.stage_changed` — Lead moved between stages
- `lead.assigned` — Lead re-assigned to new owner
- `lead.requirement_met` — Lead satisfied a requirement

### Communication Events
- `message.sent` — Outbound message delivered to channel
- `message.delivered` — Channel confirmed delivery
- `message.read` — Recipient read the message
- `message.replied` — Recipient replied
- `conversation.created` — New conversation thread started
- `conversation.assigned` — Agent assigned to conversation

### Future Architecture
- Microservices separation: Flow execution engine as standalone worker.
- Event streaming via Redis streams or RabbitMQ for reliable delivery.
- WebSocket-based real-time inbox updates.
- GraphQL for complex nested data fetching (Inbox + JAWIS context).

---

## 3. Core Principles

- **JawCom never owns CRM.** Customer data stays in JAWIS. JawCom only references lead_id.
- **JawCom never edits Lead Stage.** Lead lifecycle is JAWIS domain. JawCom only reacts.
- **JawCom reacts to JAWIS events.** Stage mappings define which journey triggers on which event.
- **Templates contain content.** Templates hold message body with `{{variable}}` placeholders.
- **Flows never contain message text.** Flow nodes reference template_id + variable_mapping only.
- **Journeys execute Flows.** A Journey maps a stage trigger to a Flow definition.
- **Campaigns are one-to-many.** Broadcast a template to N leads. Independent of Journey state machines.
- **Inbox is communication only.** No CRM editing. Read-only JAWIS context panel.
- **Customer information is read-only.** Fetched from JAWIS API, cached briefly, never mutated.
- **Single source of truth per domain.** JAWIS for business data. JawCom for communication data. No duplication.

---

## 4. Navigation

| Route | Module | Status |
|---|---|---|
| `/` | Dashboard | Implemented (static) |
| `/inbox` | Inbox | Implemented (static) |
| `/journeys` | Journeys | Implemented (static) |
| `/journeys/:id` | Journey Detail | Implemented (static) |
| `/journeys/:id/dashboard` | Journey Dashboard | Implemented (static) |
| `/journeys/:id/flow` | Flow Builder | Implemented (static) |
| `/journeys/:id/running` | Running Instances | Implemented (static) |
| `/journeys/:id/settings` | Journey Settings | Implemented (static) |
| `/campaigns` | Campaigns | Implemented (static) |
| `/templates` | Templates | Implemented (static) |
| `/reports` | Reports | Implemented (static) |
| `/knowledge` | Knowledge | Implemented (static, deferred post-V1) |
| `/assistant` | AI Assistant | Implemented (static, deferred post-V1) |
| `/integrations` | Integrations | Implemented (static) |
| `/developers` | Developers | Implemented (static) |
| `/settings` | Settings | Implemented (static) |
| `/search` | Global Search | Implemented (static) |

### Removed routes (per architecture review)
- `/contacts` — JawCom does not own customer data
- `/automation` — Merged into Journey Flow Builder
- `/automation/builder` — Duplicate of Automation
- `/customers` — Redirect to Contacts
- `/companies` — Redirect to Contacts
- `/followups` — Redirect to Journeys

### Future modules (post-V1)
- Knowledge (RAG-powered knowledge base)
- AI Assistant (AI chat, not flow nodes)

---

## 5. Module Responsibilities

### Dashboard
- **Purpose**: Overview KPIs and recent activity.
- **Responsibilities**: Display communication metrics (sent, delivered, read, replied), recent conversations, journey health, campaign performance.
- **Out of Scope**: CRM pipeline metrics, revenue data.
- **Future Scope**: Real-time metrics via WebSocket.

### Inbox
- **Purpose**: View and respond to customer messages across channels.
- **Responsibilities**: Display conversation threads, compose and send replies, show JAWIS context panel (read-only lead data), display journey state for the conversation lead.
- **Out of Scope**: Editing CRM data, managing lead stages.
- **Future Scope**: WebSocket live updates, agent assignment, typing indicators, canned responses.

### Journeys
- **Purpose**: Map JAWIS lead stages to automated communication flows.
- **Responsibilities**: Stage Mapping CRUD, Journey CRUD, Running instance monitoring, Journey health KPIs.
- **Out of Scope**: Storing message content, editing lead stages.
- **Future Scope**: Multi-flow journeys, A/B testing, journey versioning.

### Flow Builder
- **Purpose**: Design automated communication flows visually.
- **Responsibilities**: Drag-drop node canvas, node palette, properties panel, flow validation, save/publish flow definitions. One active flow per journey.
- **Out of Scope**: Standalone automation page, AI nodes, SMS/Voice nodes.
- **Future Scope**: Version management, draft/published split, AI-powered node suggestions.

### Campaigns
- **Purpose**: Broadcast one-to-many communications.
- **Responsibilities**: Campaign CRUD, audience selection (from JAWIS leads), template + variable mapping, schedule/recurring sends, delivery tracking.
- **Out of Scope**: Per-lead state machines (those are Journeys).
- **Future Scope**: Multi-channel campaigns, A/B subject testing.

### Templates
- **Purpose**: Reusable message content shared across Journeys and Campaigns.
- **Responsibilities**: Template CRUD, variable extraction, WhatsApp Meta-approval status tracking, usage tracking (which journeys/campaigns use which templates).
- **Out of Scope**: Storing inline message text in flows.
- **Future Scope**: Template editor with preview, version history, bulk upload.

### Reports
- **Purpose**: Communication analytics hub.
- **Responsibilities**: Delivery reports (sent/delivered/read/replied by channel), Journey success reports (completion rate, avg duration, failure points), Campaign analytics (delivery funnel, engagement).
- **Out of Scope**: CRM pipeline analytics, revenue attribution.
- **Future Scope**: Custom report builder, scheduled report exports.

### Integrations
- **Purpose**: Configure channel connections and third-party services.
- **Responsibilities**: WhatsApp Business API connection, Email (SMTP/Gmail) configuration, webhook endpoints.
- **Out of Scope**: OAuth for third-party CRMs, Zapier-style automation.
- **Future Scope**: Marketplace for channel plugins.

### Settings
- **Purpose**: Workspace and user configuration.
- **Responsibilities**: Workspace settings, user management, notification preferences, billing info.
- **Out of Scope**: JAWIS-side settings (lead stages, pipeline config).
- **Future Scope**: RBAC roles and permissions, audit logs.

---

## 6. Database Ownership

### Collections owned by JawCom (MongoDB)
| Collection | Purpose |
|---|---|
| `stage_mappings` | Stage key → Journey mapping (stage_key is plain string, not FK to JAWIS) |
| `journeys` | Journey definitions (name, status, settings) |
| `flow_definitions` | Flow JSON blob (one per journey, versioned) |
| `templates` | Reusable message templates |
| `template_usages` | Tracking template references across journeys/campaigns |
| `running_instances` | Active per-lead journey state machines |
| `instance_events` | Immutable audit log for every instance state change |
| `conversations` | Inbox conversation threads |
| `messages` | Individual messages within conversations |
| `campaigns` | Broadcast campaign definitions |
| `campaign_recipients` | Per-recipient campaign delivery status |
| `channels` | Channel connection configs (WhatsApp, Email) |
| `workspaces` | Multi-tenant workspace configuration |
| `users` | Workspace users and roles |

### Must NEVER be duplicated in JawCom
- Lead name, email, phone
- Company name, industry, size
- Lead stage, pipeline position
- Lead owner / assignee
- Any CRM entity data
- Any field that JAWIS owns

### Data fetched (not stored) from JAWIS
- Lead name, company, stage, owner — fetched at render time, cached 5 min
- Company details — fetched on demand

---

## 7. Backend Architecture

### Folder Structure
```
backend/
├── app/
│   ├── main.py              # FastAPI app factory
│   ├── config/
│   │   ├── settings.py      # Application settings
│   │   └── logging.py       # Logging configuration
│   ├── core/
│   │   ├── base_repository.py  # Base repository class
│   │   ├── base_service.py     # Base service class
│   │   └── dependencies.py     # FastAPI dependencies
│   ├── database/
│   │   ├── base.py          # Base model
│   │   ├── database.py      # Database connection
│   │   └── session.py       # Session management
│   ├── providers/           # Provider abstraction layer
│   │   ├── base/            # Abstract provider interfaces
│   │   │   ├── communication_provider.py
│   │   │   ├── whatsapp_provider.py
│   │   │   └── email_provider.py
│   │   ├── registry/        # Provider registry and dependency injection
│   │   │   └── provider_registry.py
│   │   ├── meta/            # Meta WhatsApp provider
│   │   │   └── meta_provider.py
│   │   ├── resend/          # Resend email provider
│   │   │   └── resend_provider.py
│   │   └── __init__.py      # Provider module exports
│   ├── communication/       # Communication engine and message orchestration
│   │   ├── communication_engine.py  # Central message sending orchestrator
│   │   ├── channel.py       # Channel definitions and management
│   │   ├── message.py       # Message models and types
│   │   ├── exceptions.py    # Communication-specific exceptions
│   │   └── __init__.py      # Communication module exports
│   ├── api/                 # Route handlers per module
│   ├── models/              # Pydantic/MongoEngine models
│   ├── services/            # Business logic layer
│   ├── engine/              # Flow execution engine
│   └── workers/             # Celery task definitions
├── tests/
├── requirements.txt
└── Dockerfile
```

### FastAPI
- Single `main.py` with `APIRouter(prefix="/api")`.
- Currently only has demo endpoints: `GET /api/`, `POST /api/status`, `GET /api/status`.
- CORS configured via `CORS_ORIGINS` env var.
- Logging configured via `logging.basicConfig`.

### Workers
- Not yet implemented.
- Planned: Celery workers for async flow execution, campaign sending, webhook delivery.

### Redis
- Not yet implemented.
- Planned: Celery broker, rate limiting, session store, real-time pub/sub for inbox.

### Celery
- Not yet implemented.
- Planned: Background task queue for flow node execution, campaign batch sends, scheduled jobs.

### Supabase
- Not used. MongoDB is the database.
- No current plans to migrate.

### Cloudinary
- Not yet integrated.
- Planned: Template media assets (images, PDFs), inbox attachments.

### Webhooks
- Inbound: JAWIS stage change events, WhatsApp delivery receipts, Email delivery receipts.
- Outbound: Notify JAWIS of message delivery/read events.
- Not yet implemented beyond static UI placeholders.

### Future backend structure
```
backend/
├── app/
│   ├── main.py              # FastAPI app factory
│   ├── config.py            # Settings/env management
│   ├── api/                 # Route handlers per module
│   │   ├── journeys.py
│   │   ├── inbox.py
│   │   ├── campaigns.py
│   │   ├── templates.py
│   │   ├── reports.py
│   │   ├── integrations.py
│   │   └── webhooks.py
│   ├── models/              # Pydantic/MongoEngine models
│   ├── services/            # Business logic layer
│   ├── channels/            # Channel abstraction (WhatsApp, Email)
│   ├── engine/              # Flow execution engine
│   └── workers/             # Celery task definitions
├── tests/
├── requirements.txt
└── Dockerfile
```

---

## 8. Frontend Architecture

### Stack
- React 19 (Create React App + CRACO)
- React Router 7 (client-side routing)
- Tailwind CSS 3.4
- shadcn/Radix UI primitives (46 components)
- lucide-react icons
- Recharts (charts)
- Framer Motion (animations)
- Sonner (toast notifications)
- clsx + tailwind-merge (className utilities)
- SWR + @tanstack/react-query (installed, not yet used)

### Folder Structure
```
frontend/src/
├── App.js                  # Root component, Routes definition
├── App.css                 # Global styles
├── index.js                # Entry point
├── index.css               # Tailwind base styles
├── pages/                  # Route-level entry points (thin delegates)
│   ├── Dashboard.jsx
│   ├── Inbox.jsx
│   ├── Journeys.jsx
│   ├── JourneyDetail.jsx   # Nested routes: dashboard, flow, running, settings
│   ├── Campaigns.jsx
│   ├── Templates.jsx
│   ├── Reports.jsx
│   ├── Knowledge.jsx       # Deferred post-V1
│   ├── Assistant.jsx       # Deferred post-V1
│   ├── Integrations.jsx
│   ├── Developers.jsx
│   ├── Settings.jsx
│   └── Search.jsx
├── modules/                # Feature modules (co-located components + hooks)
│   ├── inbox/
│   │   ├── ConversationList.jsx
│   │   ├── ConversationThread.jsx
│   │   ├── MessageComposer.jsx
│   │   ├── JawisContextPanel.jsx
│   │   ├── ChannelBadge.jsx
│   │   └── hooks/useConversations.js
│   ├── journeys/
│   │   ├── JourneyList.jsx
│   │   ├── StageMapping.jsx
│   │   ├── JourneyDashboard.jsx
│   │   ├── RunningInstances.jsx
│   │   ├── JourneySettings.jsx
│   │   ├── FlowBuilder/
│   │   │   ├── FlowCanvas.jsx
│   │   │   ├── NodePalette.jsx
│   │   │   ├── PropertiesPanel.jsx
│   │   │   ├── FlowToolbar.jsx
│   │   │   ├── FlowBuilder.jsx
│   │   │   └── nodes/ (Trigger, Delay, Condition, SendWhatsApp, SendEmail, Notification, Wait, End)
│   │   └── hooks/
│   ├── campaigns/
│   │   ├── CampaignList.jsx
│   │   ├── CampaignWizard.jsx
│   │   └── hooks/useCampaigns.js
│   ├── templates/
│   │   ├── TemplateList.jsx
│   │   ├── TemplatePreview.jsx
│   │   └── hooks/useTemplates.js
│   └── reports/
│       ├── DeliveryReport.jsx
│       ├── JourneyAnalytics.jsx
│       ├── CampaignAnalytics.jsx
│       └── hooks/useReports.js
├── components/             # Shared/generic components
│   ├── ui/                 # 46 shadcn/Radix primitives
│   ├── DataTable.jsx
│   ├── StatCard.jsx
│   ├── ChartCard.jsx
│   ├── PageHeader.jsx
│   ├── StatusBadge.jsx
│   ├── EmptyState.jsx
│   ├── LoadingSkeleton.jsx
│   ├── FilterBar.jsx
│   ├── SearchBar.jsx
│   ├── Header.jsx
│   ├── Sidebar.jsx
│   └── ThemeToggle.jsx
├── services/               # API layer (placeholder → real backend)
│   ├── index.js            # Service registry
│   ├── inbox.js
│   ├── journeys.js
│   ├── campaigns.js
│   ├── templates.js
│   ├── reports.js
│   ├── integrations.js
│   └── jawis.js            # Read-only JAWIS sync client
├── hooks/
│   ├── use-theme.js
│   └── use-toast.js
├── layouts/
│   └── AppLayout.jsx       # Sidebar + Header + Outlet
├── constants/
│   ├── nav.js              # Navigation items
│   ├── flowNodes.js        # Node type definitions
│   └── channels.js         # WhatsApp + Email channel configs
├── lib/
│   └── utils.js            # cn() utility
└── dummy-data/             # Static data (to be replaced by API calls)
    ├── index.js
    ├── journeys.js
    ├── templates.js
    ├── automation.js
    ├── companies.js
    ├── developers.js
    ├── knowledge.js
    └── ai-memory.js
```

### Theme
- Indigo-600 accent color on neutral grays.
- Light + dark mode via `next-themes`.
- Rounded-xl cards.
- Font: Plus Jakarta Sans (body) + IBM Plex Mono (code).
- Theme persisted in localStorage.

### Routing
- `BrowserRouter` with `<AppLayout>` as persistent wrapper (Sidebar + Header + `<Outlet>`).
- Journey detail uses nested routes: `/journeys/:id/{dashboard|flow|running|settings}`.
- Catch-all `*` redirects to `/`.

---

## 9. API Design Standards

### Naming
- RESTful resource-based: `/api/journeys`, `/api/templates`, `/api/campaigns`
- Plural nouns for collections: `/api/journeys`, `/api/inbox/conversations`
- Nested for sub-resources: `/api/journeys/{id}/running-instances`
- Snake_case for JSON fields: `template_id`, `flow_definition`, `variable_mapping`

### Response format
```json
{
  "data": { ... },
  "meta": {
    "page": 1,
    "per_page": 50,
    "total": 200
  }
}
```

### Error format
```json
{
  "error": {
    "code": "validation_error",
    "message": "Template body is required",
    "details": { "field": "body", "reason": "required" }
  }
}
```

### Versioning
- URL prefix: `/api/v1/` once stable.
- Early development: `/api/` prefix only.

### Authentication strategy
- JWT-based (planned).
- Workspace-scoped: all queries filtered by `workspace_id`.
- Not yet implemented.

---

## 10. Coding Standards

### Naming
- **Backend**: Snake_case for Python files, variables, functions. PascalCase for classes.
- **Frontend**: PascalCase for components and files. camelCase for functions and variables.
- **Database**: Snake_case for field names.
- **Routes**: kebab-case: `/journey-detail`, not `/journeyDetail`.
- **Environment variables**: UPPER_SNAKE_CASE.

### Comments
- No inline comments in production code unless explaining non-obvious logic.
- JSDoc/docstring for public API functions and complex business logic.

### Folder organization
- One component per file.
- Module-scoped components live inside `modules/{module}/`.
- Shared components live in `components/` (generic) or `components/ui/` (primitives).
- Pages are thin — one file per route, delegates to module components.
- No cross-module imports of internal files. Modules communicate through services layer.

### Error handling
- Backend: Global exception handler with structured error responses.
- Frontend: Service layer throws typed errors. Components handle loading/error/empty states.
- Never expose stack traces in production.

### Logging
- Backend: Structured JSON logging via Python logging module.
- Frontend: `console.error` for API failures in development; Sentry/RUM in production.

---

## 11. Current Development Status

### Completed
- Frontend: All 16+ pages with static UI and dummy data
- Frontend: AppLayout (Sidebar + Header), responsive sidebar collapse
- Frontend: Theme system (light/dark) with persistence
- Frontend: 46 shadcn/Radix UI primitives
- Frontend: 12 reusable product components
- Frontend: 5 feature modules (inbox, journeys, campaigns, templates, reports)
- Frontend: Flow Builder with visual canvas, node palette, properties panel
- Frontend: JAWIS context panel (read-only lead data display)
- Frontend: Service layer placeholder structure
- Backend: FastAPI scaffold with MongoDB connection
- Backend: Core foundation (config, database, core) - Sprint 1
- Backend: Provider abstraction layer (WhatsApp/Email providers) - Sprint 2
- Backend: Communication Engine (message orchestration, channel management) - Sprint 3

### In Progress
- Frontend architecture refactor per ARCHITECTURE.md (removing Contacts, Automation, renaming routes)
- Frontend service layer wiring to placeholder backend endpoints
- Define API contracts for all modules (OpenAPI spec)

### Pending
- Backend product APIs for every module
- Flow execution engine (graph walker for Running Instances)
- Channel integration (WhatsApp Meta Cloud API, Email SMTP/Gmail)
- Inbound webhook handlers
- Campaign execution engine
- Running Instance state machine
- Database domain models and indexes
- Retry policy, business hours, rate limiting
- Auth (JWT) and RBAC
- Real analytics pipeline

### Blocked
- Real inbox send/receive — blocked by channel integration
- Flow execution — blocked by backend domain models
- Campaign execution — blocked by audience filtering from JAWIS

---

## 12. Development Roadmap

### Current Sprint
- Architectural cleanup: remove old pages (Contacts, Automation, AutomationBuilder), update routes
- Wire frontend services to placeholder backend endpoints
- Define API contracts for all modules (OpenAPI spec)

### Next Sprint
- Build JAWIS sync client (read-only API client + webhook receiver)
- Stage Mapping CRUD (backend + frontend)
- Journey CRUD (backend + frontend)
- Flow Definition storage (JSON blob)
- Running Instance state machine

### Future Features
- Flow Execution Engine (graph walker with node executors)
- WhatsApp Channel (Meta Cloud API)
- Email Channel (SMTP / Gmail API)
- Campaign Execution Engine
- Real-time inbox via WebSocket
- Reports analytics pipeline
- Retry policy, business hours, rate limiting
- RBAC and workspace management
- Testing (unit + integration + E2E)
- Deployment configs (Docker, CI/CD)

### Deferred Features
- Knowledge base with RAG
- AI Assistant (AI chat, not flow nodes)
- AI-powered flow nodes
- SMS and Voice channels
- Developers SDK/examples
- Flow versioning (V1/V2 branching)
- Multi-flow journeys
- Marketplace for channel plugins

---

## 13. Architecture Decisions

### AD-001: JawCom does not own customer data
- **Reason**: Keep communication OS independent of any specific business OS. Avoid data duplication and sync issues.
- **Benefits**: JawCom can integrate with any CRM. No data consistency problems. Simpler data model.
- **Tradeoffs**: Requires JAWIS API availability at render time. Slightly higher latency for context panel.

### AD-002: Stage key is a plain string, not a FK to JAWIS
- **Reason**: JAWIS can add/edit stages without JawCom code changes. Loose coupling.
- **Benefits**: Zero-dependency integration. JAWIS stage renames don't break mappings.
- **Tradeoffs**: No referential integrity. UI cannot auto-complete stage names without JAWIS API call.

### AD-003: One active flow per journey in V1
- **Reason**: Simplifies execution engine, UI, and state management. Avoids version branching complexity.
- **Benefits**: Faster V1 delivery. Simpler data model. Clearer UX.
- **Tradeoffs**: Cannot run A/B flow variants. Manual version tracking required.

### AD-004: Flow stored as JSON blob, not node-by-node in relational tables
- **Reason**: Flow graphs are naturally tree structures. JSON blob matches how React Flow serializes. No complex graph queries needed in V1.
- **Benefits**: Simple storage. Easy to version (copy entire blob). Matches frontend serialization.
- **Tradeoffs**: Cannot query individual nodes via database. Requires full blob load for any operation.

### AD-005: Campaigns are separate from Journeys
- **Reason**: Different execution models — campaigns are one-to-many broadcasts, journeys are one-to-one state machines. Different data models, different scaling patterns.
- **Benefits**: Independent scaling. Clearer UX. Simpler execution engine for each.
- **Tradeoffs**: Shared templates require usage tracking across both systems.

### AD-006: Flow nodes reference template_id, not inline message text
- **Reason**: Templates are reusable assets. Keeping message text out of flows enables template approval workflows (Meta approval) without flow changes.
- **Benefits**: Templates can be updated independently. Meta approval only needed once per template. Usage tracking enables impact analysis before editing.
- **Tradeoffs**: Slightly more complex send-time resolution (template lookup + variable mapping).

### AD-007: Running Instance as isolated per-lead state machine
- **Reason**: No cross-lead state ensures horizontal scalability. Workers can process instances independently.
- **Benefits**: Simple execution model. No distributed locking. Easy to retry individual instances.
- **Tradeoffs**: Cannot do cross-lead operations (e.g., "pause all instances of journey X") without bulk queries.

### AD-008: Frontend module structure with service layer
- **Reason**: Modules co-locate related components (inbox, journeys, etc.). Service layer abstracts API calls, enabling easy switch from dummy data to real backend.
- **Benefits**: Organized codebase. Easy to test services in isolation. Clear dependency direction.
- **Tradeoffs**: More files than flat structure. Requires discipline to avoid cross-module imports.

### AD-009: Plain string stage_key replaces FK to JAWIS stages
- **Reason**: JAWIS stage names are business-configurable strings. A FK would require JAWIS to expose stage IDs and maintain referential integrity across systems.
- **Benefits**: JAWIS can freely rename/reorganize stages. Stage mapping in JawCom is simple key-value.
- **Tradeoffs**: If JAWIS deletes a stage, corresponding JawCom mappings become orphaned. UI should surface unmatched mappings.

### AD-010: Provider abstraction layer for communication channels
- **Reason**: Support multiple WhatsApp and Email providers without changing business logic. Enable easy switching between providers (Meta vs Twilio for WhatsApp, Resend vs SendGrid for Email).
- **Benefits**: Vendor independence. Easy A/B testing of providers. Graceful fallback if primary provider fails. Clean separation of provider logic from business logic.
- **Tradeoffs**: Additional abstraction layer adds complexity. Provider-specific features may not be exposed through common interface.

---

## 14. Changelog

| Date | Module | Reason | Files Changed | Architecture Impact |
|---|---|---|---|---|
| 2026-07-02 | ALL | Initial master context document created | `AI_CONTEXT/JAWCOM_MASTER_CONTEXT.md` | N/A — foundation document |
| 2026-07-03 | Backend | Sprint 1: Create backend foundation | `backend/app/config/settings.py`, `backend/app/config/logging.py`, `backend/app/database/base.py`, `backend/app/database/database.py`, `backend/app/database/session.py`, `backend/app/core/base_repository.py`, `backend/app/core/base_service.py`, `backend/app/core/dependencies.py`, `backend/app/main.py`, `backend/requirements.txt`, `AI_CONTEXT/JAWCOM_MASTER_CONTEXT.md` | Added core backend foundation with Clean Architecture, Repository Pattern, and Service Layer |
| 2026-07-02 | Backend | Sprint 2: Create provider abstraction layer | `backend/app/providers/base/communication_provider.py`, `backend/app/providers/base/whatsapp_provider.py`, `backend/app/providers/base/email_provider.py`, `backend/app/providers/registry/provider_registry.py`, `backend/app/providers/meta/meta_provider.py`, `backend/app/providers/resend/resend_provider.py`, `backend/app/providers/__init__.py`, `AI_CONTEXT/JAWCOM_MASTER_CONTEXT.md` | Added provider abstraction layer enabling multiple WhatsApp/Email providers without changing business logic. Implemented MetaProvider (WhatsApp) and ResendProvider (Email) with dependency injection via ProviderRegistry |
| 2026-07-02 | Backend | Sprint 3: Create Communication Engine | `backend/app/communication/communication_engine.py`, `backend/app/communication/channel.py`, `backend/app/communication/message.py`, `backend/app/communication/exceptions.py`, `backend/app/communication/__init__.py`, `AI_CONTEXT/JAWCOM_MASTER_CONTEXT.md` | Added Communication Engine as central orchestrator for message sending. Uses ProviderRegistry for dependency injection. Handles channel management, message validation, and send orchestration. Never calls providers directly. |

---

## 15. Update Instructions

### Who should update this file
Any AI agent or developer making architecture-impacting changes.

### When to update
Append a new entry to the Changelog (section 14) whenever any of the following occurs:
1. New module added or existing module removed
2. Database schema changes (new collections, field changes, index changes)
3. API contract changes (new endpoints, response format changes, auth changes)
4. Architecture decisions (new AD entries in section 13)
5. Technology stack changes (new dependencies, framework migrations)
6. Navigation/routing changes
7. Module responsibility changes
8. Development status changes (completed → in-progress, etc.)
9. Roadmap changes (new sprints, reprioritized features)

### How to update
1. Read the current `JAWCOM_MASTER_CONTEXT.md` in full first.
2. Make targeted edits — do not rewrite the entire document unless restructuring is needed.
3. Always append to the Changelog with today's date, the module affected, the reason, files changed (relative repo paths), and the architecture impact summary.
4. Update section 11 (Current Development Status) to reflect progress accurately.
5. If adding a new architecture decision, append to section 13 with the next AD number.

### Document maintenance rules
- Keep concise. No prose beyond what's needed. Use tables and lists.
- Never repeat information in multiple sections — reference by section number.
- Remove completed roadmap items from "Future Features" when they ship.
- Update Development Status immediately when a feature transitions.
- Archive deferred features to the "Deferred Features" section, don't delete them.
- If this document grows beyond ~500 lines, consider splitting into sub-documents in `AI_CONTEXT/` with cross-references.

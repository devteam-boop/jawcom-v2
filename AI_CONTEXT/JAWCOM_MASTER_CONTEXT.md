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
v0.1.0 — Frontend prototype with dummy data. Backend with service-layer modules and domain models.

### Development Status
- **Frontend static UI**: ~70% complete (all pages, components, routing, theme)
- **Frontend API wiring**: ~10% complete (service layer defined, not connected)
- **Backend foundation (config/database/core)**: ~100% complete
- **Backend provider abstraction (WhatsApp/Email)**: ~100% complete (abstract + Meta implementation)
- **Backend communication engine**: ~100% complete (engine + mock provider)
- **Backend event system + JAWIS integration**: ~100% complete
- **Backend domain models (SQLAlchemy)**: ~80% complete (11 tables defined)
- **Backend business modules (Journeys, Flows, Templates, Stage Mapping, Runtime)**: ~70% complete (services/schemas/validators, no API routes)
- **Backend product API routes**: ~5% complete (only /health endpoint)
- **Auth/Security**: 0% complete
- **Integrations (WhatsApp/Email real API calls)**: 0% complete (placeholder implementations)
- **Overall product**: ~35% complete

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

### Tables owned by JawCom (PostgreSQL via SQLAlchemy 2.0 Async)
| Table | Purpose | Status |
|---|---|---|
| `workspaces` | Multi-tenant workspace configuration | Implemented |
| `users` | Workspace users and roles | Implemented |
| `journeys` | Journey definitions (name, status, settings) | Implemented |
| `flow_definitions` | Flow JSON blob (one per journey) | Implemented |
| `templates` | Reusable message templates | Implemented |
| `stage_mappings` | Stage key → Journey mapping | Implemented |
| `running_journey_instances` | Active per-lead journey state machines | Implemented |
| `conversations` | Inbox conversation threads | Implemented |
| `messages` | Individual messages within conversations | Implemented |
| `campaigns` | Broadcast campaign definitions | Implemented |
| `campaign_recipients` | Per-recipient campaign delivery status | Implemented |
| `instance_events` | Immutable audit log | TODO (not yet modeled) |
| `template_usages` | Tracking template references | TODO (not yet modeled) |
| `channels` | Channel connection configs | TODO (not yet modeled) |

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
│   ├── main.py              # FastAPI app entry point, /health endpoint
│   ├── pipeline.py          # Event processing pipeline
│   ├── config/
│   │   ├── __init__.py      # Settings export
│   │   ├── settings.py      # Pydantic settings (PostgreSQL async)
│   │   └── logging.py       # Logging configuration
│   ├── core/
│   │   ├── __init__.py
│   │   ├── base_repository.py  # Base repository with CRUD
│   │   ├── base_service.py     # Abstract base service
│   │   └── dependencies.py     # FastAPI DB session dependency
│   ├── database/
│   │   ├── base.py          # SQLAlchemy DeclarativeBase
│   │   ├── database.py      # Async engine factory
│   │   └── session.py       # Async session maker + init/close
│   ├── providers/           # Provider abstraction layer (Sprint 2)
│   │   ├── __init__.py      # Module exports
│   │   ├── base/
│   │   │   ├── communication_provider.py  # Abstract base class
│   │   │   ├── whatsapp_provider.py       # Abstract WhatsApp provider
│   │   │   └── email_provider.py          # Abstract Email provider
│   │   ├── registry/
│   │   │   └── provider_registry.py       # DI container for providers
│   │   └── meta/
│   │       └── meta_provider.py           # Meta WhatsApp (placeholder)
│   │   # NOTE: ResendProvider referenced in __init__.py but file missing
│   ├── communication/       # Communication engine (Sprint 3)
│   │   ├── engine.py        # CommunicationEngine orchestrator
│   │   ├── providers.py     # Mock WhatsApp provider (local)
│   │   └── __init__.py
│   ├── events/              # Event system (Sprint 4)
│   │   ├── base_event.py    # BaseEvent + EventHandler ABCs
│   │   ├── event_types.py   # Typed JAWIS events (LeadCreated, etc.)
│   │   ├── dispatcher.py    # EventDispatcher with queuing + retry
│   │   ├── handlers.py      # CommunicationEventHandler + Logging + Metrics
│   │   └── __init__.py
│   ├── jawis/               # JAWIS integration (Sprint 4)
│   │   ├── client.py        # JawisClient (read-only API + caching)
│   │   ├── webhook.py       # JawisWebhookHandler
│   │   ├── schemas.py       # Pydantic schemas
│   │   └── __init__.py
│   ├── journeys/            # Journey Engine business module
│   │   ├── services.py      # JourneyService CRUD
│   │   ├── schemas.py       # Pydantic schemas
│   │   ├── validators.py    # JourneyValidator
│   │   ├── journey_manager.py # Activate/pause/archive logic
│   │   ├── exceptions.py
│   │   └── __init__.py
│   ├── flows/               # Flow Definition Engine business module
│   │   ├── services.py      # FlowService CRUD + publish
│   │   ├── schemas.py       # Pydantic schemas + node types
│   │   ├── validators.py    # FlowValidator (circular refs, orphans)
│   │   ├── flow_builder.py  # FlowBuilder helper
│   │   ├── exceptions.py
│   │   └── __init__.py
│   ├── templates/           # Template Engine business module
│   │   ├── services.py      # TemplateService CRUD + render
│   │   ├── schemas.py       # Pydantic schemas
│   │   ├── validators.py    # TemplateValidator (variables, syntax)
│   │   ├── renderer.py      # TemplateRenderer (Jinja2)
│   │   ├── exceptions.py
│   │   └── __init__.py
│   ├── stage_mapping/       # Stage Mapping Engine business module
│   │   ├── services.py      # StageMappingService CRUD
│   │   ├── schemas.py       # Pydantic schemas
│   │   ├── validators.py    # StageMappingValidator
│   │   ├── mapping_manager.py # Enable/disable + query logic
│   │   ├── exceptions.py
│   │   └── __init__.py
│   ├── runtime/             # Running Journey Instance Engine
│   │   ├── services.py      # RunningInstanceService CRUD
│   │   ├── schemas.py       # Pydantic schemas + status enum
│   │   ├── validators.py    # RunningInstanceValidator
│   │   ├── instance_manager.py # Pause/resume/cancel/complete
│   │   ├── exceptions.py
│   │   └── __init__.py
│   ├── models/              # SQLAlchemy models (11 tables)
│   │   ├── base.py          # BaseModel with UUID PK, timestamps
│   │   ├── workspace.py     # Workspace
│   │   ├── user.py          # User + UserRole
│   │   ├── journey.py       # Journey + JourneyStatus
│   │   ├── template.py      # Template + TemplateChannel/Status
│   │   ├── flow_definition.py # FlowDefinition (JSON blob)
│   │   ├── stage_mapping.py # StageMapping
│   │   ├── running_journey_instance.py # RunningJourneyInstance + InstanceStatus
│   │   ├── conversation.py  # Conversation + ConversationChannel
│   │   ├── message.py       # Message + MessageDirection/Status
│   │   ├── campaign.py      # Campaign + CampaignStatus
│   │   ├── campaign_recipient.py # CampaignRecipient + RecipientStatus
│   │   └── __init__.py      # All model exports
│   └── workers/             # Empty (future Celery tasks)
├── server.py                # Entry point (merge conflict exists)
├── requirements.txt         # FastAPI, SQLAlchemy 2.0 async, asyncpg
├── pytest.ini
└── .env                     # Legacy MongoDB config (needs update for PostgreSQL)
```

### FastAPI
- Single `main.py` with `GET /health` endpoint.
- CORS configured via `CORS_ORIGINS` env var.
- Logging configured via `app/config/logging.py`.
- Database: PostgreSQL with SQLAlchemy 2.0 async + asyncpg.
- No product API routes implemented yet (services exist but no endpoints).

### Workers
- Not yet implemented. Empty `backend/app/workers/` directory.
- Planned: Celery workers for async flow execution, campaign sending, webhook delivery.

### Redis
- Not yet implemented.
- Planned: Celery broker, rate limiting, session store, real-time pub/sub for inbox.

### Celery
- Not yet implemented.
- Planned: Background task queue for flow node execution, campaign batch sends, scheduled jobs.

### Database
- PostgreSQL via SQLAlchemy 2.0 Async + asyncpg.
- 11 tables defined: workspaces, users, journeys, flow_definitions, templates, stage_mappings, running_journey_instances, conversations, messages, campaigns, campaign_recipients.
- Legacy `.env` still has MongoDB config. Settings class expects `DATABASE_URL` for PostgreSQL.

### Cloudinary
- Not yet integrated.
- Planned: Template media assets (images, PDFs), inbox attachments.

### Webhooks
- Inbound: JAWIS stage change events handled via `jawis/webhook.py` → `events/dispatcher.py`.
- Outbound: Notify JAWIS of message delivery/read events — not yet implemented.
- JAWIS webhook handler exists with batch processing and signature validation placeholder.

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
- Backend: Core foundation (config, database, core) — Sprint 1
- Backend: Provider abstraction layer (WhatsApp/Email providers) — Sprint 2
- Backend: Communication Engine (message orchestration) — Sprint 3
- Backend: Event System (business event handling, JAWIS integration) — Sprint 4
- Backend: SQLAlchemy domain models (11 tables) — Sprint 5
- Backend: Journey Engine (JourneyService, JourneyManager, validators) — Sprint 5
- Backend: Flow Definition Engine (FlowService, FlowBuilder, validators) — Sprint 5
- Backend: Template Engine (TemplateService, TemplateRenderer, validators) — Sprint 5
- Backend: Stage Mapping Engine (StageMappingService, MappingManager) — Sprint 5
- Backend: Running Instance Engine (RunningInstanceService, InstanceManager) — Sprint 5
- Backend: Pipeline module for event processing — Sprint 5

### In Progress
- Frontend architecture refactor per ARCHITECTURE.md (removing Contacts, Automation, renaming routes)
- Frontend service layer wiring to placeholder backend endpoints
- Define API contracts for all modules (OpenAPI spec)
- Fix merge conflict in `backend/server.py`
- Fix missing `backend/app/providers/resend/resend_provider.py` (imported but missing)
- Migrate `.env` from legacy MongoDB config to PostgreSQL `DATABASE_URL`

### Pending
- Backend product API routes (all services need HTTP endpoints)
- Flow execution engine (graph walker for Running Instances)
- Running Instance state machine wiring (exists as service, not wired to execution)
- Channel real integration (WhatsApp Meta Cloud API, Email SMTP/Gmail)
- Campaign execution engine
- Auth (JWT) and RBAC
- Retry policy, business hours, rate limiting enforcement
- Real analytics pipeline
- Workers/Celery for async tasks
- `instance_events`, `template_usages`, `channels` tables
- Webhook signature validation

### Blocked
- Real inbox send/receive — blocked by channel integration
- Flow execution — blocked by flow execution engine
- Campaign execution — blocked by audience filtering from JAWIS

---

## 12. Development Roadmap

### Current Sprint
- Resolve merge conflict in `backend/server.py` (old MongoDB scaffold vs new app.main)
- Create missing `backend/app/providers/resend/resend_provider.py`
- Update `.env` for PostgreSQL `DATABASE_URL`
- Wire frontend services to placeholder backend endpoints
- Define API contracts for all modules (OpenAPI spec)

### Next Sprint
- Build backend product API routes for all business modules (journeys, flows, templates, stage_mapping, runtime)
- Connect service layer to FastAPI route handlers
- Build Flow Execution Engine (graph walker with node executors)
- Wire events/dispatcher to trigger journey instances on JAWIS events

### Future Features
- WhatsApp Channel (Meta Cloud API — real integration)
- Email Channel (SMTP / Gmail API — real integration)
- Campaign Execution Engine
- Running Instance state machine wiring
- Real-time inbox via WebSocket
- Reports analytics pipeline
- Retry policy, business hours, rate limiting
- Auth (JWT) and RBAC
- Workers/Celery for async tasks
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
| 2026-07-02 | Backend | Sprint 4: Create Event System | `backend/app/events/base_event.py`, `backend/app/events/event_types.py`, `backend/app/events/dispatcher.py`, `backend/app/events/handlers.py`, `backend/app/events/__init__.py`, `backend/app/jawis/client.py`, `backend/app/jawis/webhook.py`, `backend/app/jawis/schemas.py`, `backend/app/jawis/__init__.py`, `AI_CONTEXT/JAWCOM_MASTER_CONTEXT.md` | Added Event System for handling business events from JAWIS. Includes typed event models, event dispatcher, JAWIS API client, and webhook handler. Communication Engine can now subscribe to business events. |
| 2026-07-03 | Backend | Sprint 5: Create business domain models (SQLAlchemy) | `backend/app/models/base.py`, `backend/app/models/workspace.py`, `backend/app/models/user.py`, `backend/app/models/journey.py`, `backend/app/models/template.py`, `backend/app/models/flow_definition.py`, `backend/app/models/stage_mapping.py`, `backend/app/models/running_journey_instance.py`, `backend/app/models/conversation.py`, `backend/app/models/message.py`, `backend/app/models/campaign.py`, `backend/app/models/campaign_recipient.py`, `backend/app/models/__init__.py`, `AI_CONTEXT/JAWCOM_MASTER_CONTEXT.md` | Created 11 SQLAlchemy domain models covering all JawCom data domains. PostgreSQL UUID primary keys, proper relationships, enums. |
| 2026-07-03 | Backend | Sprint 5: Create Journey Engine | `backend/app/journeys/services.py`, `backend/app/journeys/schemas.py`, `backend/app/journeys/validators.py`, `backend/app/journeys/journey_manager.py`, `backend/app/journeys/exceptions.py`, `backend/app/journeys/__init__.py`, `AI_CONTEXT/JAWCOM_MASTER_CONTEXT.md` | Journey Engine with CRUD service, state management (activate/pause/archive), validation, and trigger-based lookup. |
| 2026-07-03 | Backend | Sprint 5: Create Flow Definition Engine | `backend/app/flows/services.py`, `backend/app/flows/schemas.py`, `backend/app/flows/validators.py`, `backend/app/flows/flow_builder.py`, `backend/app/flows/exceptions.py`, `backend/app/flows/__init__.py`, `AI_CONTEXT/JAWCOM_MASTER_CONTEXT.md` | Flow Definition Engine with CRUD, publish/version management, FlowBuilder helper, validation (circular references, orphan nodes, template references). |
| 2026-07-03 | Backend | Sprint 5: Create Template Engine | `backend/app/templates/services.py`, `backend/app/templates/schemas.py`, `backend/app/templates/validators.py`, `backend/app/templates/renderer.py`, `backend/app/templates/exceptions.py`, `backend/app/templates/__init__.py`, `AI_CONTEXT/JAWCOM_MASTER_CONTEXT.md` | Template Engine with CRUD, Jinja2-based rendering, variable extraction, email/WhatsApp validation. |
| 2026-07-03 | Backend | Sprint 5: Create Stage Mapping Engine | `backend/app/stage_mapping/services.py`, `backend/app/stage_mapping/schemas.py`, `backend/app/stage_mapping/validators.py`, `backend/app/stage_mapping/mapping_manager.py`, `backend/app/stage_mapping/exceptions.py`, `backend/app/stage_mapping/__init__.py`, `AI_CONTEXT/JAWCOM_MASTER_CONTEXT.md` | Stage Mapping Engine with CRUD, trigger-based lookup, business hours/retry policy config. |
| 2026-07-03 | Backend | Sprint 5: Create Running Instance Engine | `backend/app/runtime/services.py`, `backend/app/runtime/schemas.py`, `backend/app/runtime/validators.py`, `backend/app/runtime/instance_manager.py`, `backend/app/runtime/exceptions.py`, `backend/app/runtime/__init__.py`, `AI_CONTEXT/JAWCOM_MASTER_CONTEXT.md` | Running Instance Engine with CRUD, state management (pause/resume/cancel/complete), duplicate prevention. |
| 2026-07-03 | Backend | Sprint 5: Create Pipeline module | `backend/app/pipeline.py`, `AI_CONTEXT/JAWCOM_MASTER_CONTEXT.md` | Pipeline for processing JAWIS events through the complete communication chain. |
| 2026-07-03 | Backend | Add missing FK on flow_execution_logs.running_instance_id | `backend/app/models/flow_execution_log.py`, `backend/alembic/versions/b3c4d5e6f7a8_add_fk_running_instance_id.py`, `AI_CONTEXT/JAWCOM_MASTER_CONTEXT.md` | Added foreign key constraint ensuring referential integrity between flow execution logs and running journey instances. |

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

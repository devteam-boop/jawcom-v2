# JAWCOM — Architecture

> **This is the canonical architecture reference for JAWCOM.** For related
> documentation see `AI_CONTEXT.md` (quick-reference/golden rules),
> `module_dependencies.md` (dependency graph/rules), `roadmap.md` /
> `sprint_status.md` (what's done vs planned), `decisions.md` (ADRs),
> `KNOWN_ISSUES.md` (tech debt), `api_contract.md` (live REST surface).
>
> Three older documents are **archived and superseded** by this file — do not
> use them for current-state decisions: root `ARCHITECTURE.md` (a 2026-07-02
> redesign proposal, never fully implemented), root `PROJECT_REVIEW.md` (an
> early-prototype snapshot, now obsolete), and `AI_CONTEXT/JAWCOM_MASTER_CONTEXT.md`
> (a Sprint 1-5 era snapshot). Each carries a banner pointing back here.

## System Overview

JAWCOM is a journey automation platform. Business events (lead stage changes from JAWIS Business OS) trigger configurable flows. Flows are visually built in a ReactFlow-based Flow Builder, validated, published, and executed by a pluggable executor engine.

### High-Level Flow

```
JAWIS Webhook / Test Call
       │
       ▼
Stage Mapping (stage_key → journey_id)
       │
       ▼
Journey (must be ACTIVE)
       │
       ▼
Flow Definition (published JSON graph)
       │
       ▼
Validation (static graph + node config checks)
       │
       ▼
Execution Engine (BFS traversal)
       │
       ├── Executor Factory (dispatches by node_type)
       │     ├── TriggerExecutor
       │     ├── ConditionExecutor    ← real comparison engine
       │     ├── DelayExecutor        ← stores resume_at, status=skipped
       │     ├── WaitExecutor         ← pauses instance, status=skipped
       │     ├── SendWhatsAppExecutor ← resolves template_id via exec_ctx.template_service, delegates to integration
       │     ├── SendEmailExecutor    ← resolves template_id via exec_ctx.template_service, delegates to integration
        │     ├── NotificationExecutor ← builds request, delegates to integration
        │     ├── EndExecutor
        │     ├── ApprovalExecutor     ← NEW: pauses for human approval (status=skipped, _halt=approval)
        │     └── ManualTaskExecutor   ← NEW: pauses for human task (status=skipped, _halt=task)
        │
         ├── Integration Layer (app/integrations/)
         │     ├── IntegrationFactory (registry + alias resolution)
         │     │     └── "crm" alias resolved by env var:
         │     │           JAWIS_CRM_PROVIDER=dummy → crm_dummy
         │     │           JAWIS_CRM_PROVIDER=jawis → crm_jawis
         │     ├── JawisWhatsAppIntegration ← "whatsapp" (default): live JAWIS API (POST /api/messages/whatsapp/send)
         │     ├── JawisEmailIntegration    ← "email" (default): live JAWIS API (POST /api/messages/email/send)
         │     ├── WhatsAppIntegration      ← "whatsapp_dummy": simulated, logs payload
         │     ├── EmailIntegration         ← "email_dummy": simulated, logs payload
         │     ├── NotificationIntegration  ← simulated, logs payload
         │     ├── DummyCRMIntegration      ← simulated, logs payload
         │     ├── JawisCRMIntegration      ← live JAWIS API (PATCH /api/leads/:id)
         │     └── IntegrationConfig        ← secrets from env (incl. JAWIS_BASE_URL/JAWIS_API_TOKEN)
         │
         ├── LeadProviderFactory
         │     ├── JAWIS_LEAD_PROVIDER=dummy → DummyLeadProvider
         │     └── JAWIS_LEAD_PROVIDER=jawis → JawisLeadProvider (wraps JawisClient)
        ├── VariableResolverService (dotted-path lookup)
        ├── TemplateRendererService ({{...}} replacement)
        ├── TemplateService (NEW Sprint 18: resolves node.config.template_id → Template row, attached to ExecutionContext)
        ├── ExecutionContext (passed to every executor)
        ├── SchedulerService (background poller → resumes waiting instances)
        ├── RetryService (node-level and journey-level retry)
        ├── ApprovalService (NEW: manages approvals in instance.data JSON)
        └── TaskService (NEW: manages tasks in instance.data JSON)
               │
               ▼
        Running Instance (status: running/completed/failed/waiting/waiting_approval/waiting_task)
               │
               ▼
        Execution Logs (one "started" + one "success|failed|skipped" per node)
               │
               ▼
        Execution Monitor (React dashboard) — Frontend
               │
               ├── Overview Tab — status badges for waiting_approval/waiting_task
               ├── Approvals Tab — list approvals, Approve/Reject buttons
               ├── Tasks Tab — list tasks, Complete/Reject buttons
               ├── Steps Tab — node status indicators
               ├── Timeline Tab — chronological log entries
               └── Raw JSON Tab — debug view
```

## Module Boundaries

### Backend Modules (`backend/app/`)

| Module | Responsibility | Depends On |
|---|---|---|
| `api/` | FastAPI route handlers | services/ |
| `services/` | Business logic, validation, variable resolution, scheduler, retry | models/, repositories/ |
| `models/` | SQLAlchemy ORM models | database/ |
| `repositories/` | Data access layer | models/ |
| `execution/` | Engine, executor framework, providers | services/, models/ |
| `execution/executors/` | Individual node executors | execution/executors/base.py |
| `execution/providers/` | LeadProvider interface + factory | (stdlib) |
| `integrations/` | External service adapters, factory, config | config/ (settings) |
| `templates/` | `TemplateService`/`TemplateValidator`/`TemplateRenderer` — CRUD, Jinja2-based `{{var}}` rendering for the `templates` table (single template model, Sprint 18) | repositories/, models/ |
| `events/` | Typed JAWIS business events, `EventDispatcher`, `CommunicationEventHandler` — routes inbound webhook events to the Execution Engine. See "Event Dispatch Architecture" below. | execution/ (`CommunicationEventHandler` constructs an `ExecutionEngine` directly — not via services/) |
| `jawis/` | JAWIS webhook receiver + payload normalization (inbound); JAWIS API client (outbound, external system) | config/, events/ |
| `flows/` | Flow builder/manager (legacy — still constructs the old sync `TemplateService(Session)`, unused) | — |
| `journeys/` | Journey manager (legacy) | — |
| `stage_mapping/` | Stage mapping manager (legacy) | — |
| `runtime/` | Running instance schemas/validators | models/ |
| `config/` | Settings, logging | — |
| `database/` | Session management, base model | — |
| `core/` | Base repository, dependencies | database/ |
| `providers/` | **Dormant, unused scaffold.** A second provider abstraction (`ProviderRegistry`, `Channel`, `MetaProvider`, `ResendProvider`) that predates `integrations/` and was never wired to it — nothing in the live app imports `app.providers`. Its `ResendProvider` import is currently broken (`resend/resend_provider.py` doesn't exist on disk — see `KNOWN_ISSUES.md` #8). Do not build on this; extend `integrations/` instead. | — |
| `communication/` | **Dormant, unused scaffold.** `CommunicationEngine` + a mock `WhatsAppProvider`, predating the real `SendWhatsAppExecutor`/`JawisWhatsAppIntegration` path. Never instantiated anywhere; calls `TemplateService` with an outdated synchronous signature (see `KNOWN_ISSUES.md` #7). Not part of any live request path. | — |

### Frontend Modules (`frontend/src/`)

| Module | Responsibility |
|---|---|
| `pages/JourneyMonitor.jsx` | Global operations monitor — table of all running instances across every journey; opens `ExecutionDrawer` on row click |
| `pages/Templates.jsx` | Template Library — list/create/edit/delete/duplicate/archive/preview, wired to `/api/templates` |
| `modules/journeys/` | Journey list, Flow Builder, hooks |
| `modules/journeys/JourneyDashboard.jsx` | Journey Dashboard tab — high-level overview only: Journey Summary, Execution Metrics (aggregated), Flow Summary, Integration Status, Quick Actions. No per-instance/execution detail (see `ExecutionDrawer`) |
| `modules/journeys/RunningInstances.jsx` | Running tab — execution table only; opens `ExecutionDrawer` on row click |
| `modules/journeys/ExecutionDrawer.jsx` | Single reusable execution detail drawer (Overview/Approvals/Tasks/Steps/Timeline/Raw + Retry/Resume/Approve/Reject actions), shared by `RunningInstances` and `JourneyMonitor` — self-contained, fetches by `instanceId` alone |
| `modules/journeys/FlowBuilder/` | ReactFlow canvas, Properties Panel (template selector for Send WhatsApp/Send Email), Toolbar |
| `modules/templates/` | `useTemplates` hook (fetches by channel) |
| `components/` | Shared UI (DataTable, StatusBadge, SearchBar, FilterBar) |
| `components/ui/` | shadcn/ui primitives |
| `services/` | API client wrappers |

## Dependency Rules

```
routes → services → repositories → models
                         ↕
                  execution/ (engine + executors)
                         │
                         ▼
            services/ (variable_resolver, template_renderer)
                         │
                         ▼
            execution/providers/ (LeadProviderFactory)
```

- **Routes** never contain business logic
- **Routes** never call repositories directly
- **Services** are the only layer that calls repositories
- **Execution Engine** never contains node business logic
- **Executors** never call repositories or services directly
- **Executors** never call external APIs directly (delegate to IntegrationFactory)
- **Integrations** are the only layer that calls external APIs
- **Validation** never executes nodes
- **Engine** never calls external APIs (WhatsApp, SMTP)
- **LeadProviderFactory** is the only way to get a provider (never instantiate directly)
- **IntegrationFactory** is the only way to get an integration (never instantiate directly)

## Event Dispatch Architecture

The webhook endpoint (`POST /api/webhooks/jawis`, `app/main.py`) is a thin
wrapper — all normalization and routing logic lives in `app/jawis/webhook.py`
and `app/events/`.

```
POST /api/webhooks/jawis  (raw dict body)
    │
    ▼
JawisWebhookHandler.handle_webhook()        (app/jawis/webhook.py)
    │
    ├── normalize_jawis_payload(payload)
    │     ├── already {event_id, event_type, data, ...}?  → pass through unchanged (legacy shape)
    │     ├── {"event": "lead.stage_changed", "lead_id", "old_stage", "new_stage"}?
    │     │     → rewritten to {event_id (generated), event_type, timestamp, source, data: {lead_id (stringified), from_stage_key, to_stage_key}}
    │     └── anything else → passed through unchanged (fails validation below, reported as "unsupported event type")
    │
    ▼
WebhookEventSchema(**normalized)            (app/jawis/schemas.py — validates shape)
    │
    ▼
create_event_from_type(event_type, ...)     (app/events/event_types.py)
    │        via EVENT_TYPE_REGISTRY: "lead.created" | "lead.stage_changed" | "lead.assigned" | "lead.requirement_met"
    ▼
LeadCreatedEvent | LeadStageChangedEvent | LeadAssignedEvent | LeadRequirementMetEvent   (app/events/event_types.py, subclasses of BaseEvent)
    │
    ▼
EventDispatcher.dispatch(event)             (app/events/dispatcher.py, singleton via get_dispatcher())
    │
    ├── event.validate_payload()            (per-event-type required-field check)
    ├── get_handlers(event.get_event_key())  → handlers registered for this event type
    │
    ▼
CommunicationEventHandler.handle(event)     (app/events/handlers.py)
    │
    ├── LeadCreatedEvent        → engine.handle_lead_created(event)
    ├── LeadStageChangedEvent   → engine.handle_lead_stage_changed(event)
    ├── LeadAssignedEvent       → logged only (assignment notifications not implemented)
    └── LeadRequirementMetEvent → logged only (requirement-based journeys not implemented)
    │
    ▼
ExecutionEngine._execute_for_stage(lead_id, stage_key)   (see "Data Flow: Execution" below)
```

**Handler registration** happens once, at FastAPI startup (`app/main.py`
`startup_event()`): a single `CommunicationEventHandler` instance is
registered against all four event-type strings on the process-global
dispatcher (`get_dispatcher()`). There is no per-request registration and no
persistence of the handler registry — a process restart re-registers from
scratch.

**Two other handlers exist but are not registered anywhere in the app**:
`LoggingEventHandler` and `MetricsEventHandler` (`app/events/handlers.py`).
They implement the same `EventHandler` interface and could be attached via
`dispatcher.register_handler(event_type, handler)` if audit logging or
in-memory metrics are ever needed — no dispatcher changes required.

**Retry note**: `EventDispatcher` has its own `retry_count`/`max_retries`
bookkeeping on `BaseEvent` (`increment_retry()`, `should_retry()`) and a
`queue_event()`/`process_queue()` pair, but nothing in the app ever calls
`process_queue()` — the webhook path always calls `dispatch()` directly and
synchronously. This retry/queue machinery is currently inert, separate from
(and not to be confused with) `RetryService` (which retries failed *journey
nodes*, not failed *event dispatch*).

## Data Flow: Stage Mapping

```
Webhook (stage_key="qualified")
    │
    ▼
StageMappingRepository.get_by_stage_key("qualified")
    │
    ▼
Returns: [Mapping(journey_id=UUID, stage_key="qualified")]
    │
    ▼
For each mapping → load Journey → create RunningInstance → execute flow
```

## Data Flow: Execution

```
Engine._execute_for_stage(lead_id, stage_key)
    │
    ├── LeadProviderFactory.get_provider()
    │     ├── DummyLeadProvider.get_lead_context(lead_id)     [if JAWIS_LEAD_PROVIDER=dummy]
    │     │     → {"lead": {id, name, email, phone}, "company": {name, industry}}
    │     └── JawisLeadProvider.get_lead_context(lead_id)     [if JAWIS_LEAD_PROVIDER=jawis]
    │           → wraps JawisClient.get_lead_context()
    │           → same dict shape as DummyLeadProvider
    │
    ├── Build ExecutionContext
    │     ├── VariableResolverService(context_dict)
    │     └── TemplateRendererService(resolver)
    │
    ├── _resolve_first_node(definition) → trigger_node_id
    │
    ├── _execute_node(trigger_node, instance, exec_ctx, ...)
    │     ├── Create "started" FlowExecutionLog
    │     ├── ExecutorFactory.get("trigger") → TriggerExecutor
    │     ├── result = executor.execute(node, ..., exec_ctx=exec_ctx)
    │     │     └── (for action executors)
    │     │           ├── Build request payload (resolved variables)
    │     │           ├── IntegrationFactory.get("whatsapp"|"email"|"notification")
    │     │           ├── integration.execute(request)
    │     │           └── Return provider_response in output
    │     ├── Create "success|failed" FlowExecutionLog
    │     ├── Store node output in exec_ctx.node_outputs
    │     └── Update instance.data.current_node_id
    │
    └── _traverse_flow(definition, instance, exec_ctx, ...)
          └── BFS over edges, calling _execute_node for each
                └── Stop when: end node | executor fails | skipped (wait/delay) | no more nodes

When a Wait or Delay node returns ``status="skipped"``:
    └── Engine reads ``updated_context.resume_at``
    └── Wait: ``instance_service.wait()`` → status=waiting, store resume_at
    └── Delay: ``instance_service.update()`` → store resume_at (stays running)
    └── Returns False → traversal stops

Background Scheduler (SchedulerService):
    └── Polls every 30s for status=waiting instances where resume_at ≤ now
    └── Calls ``engine.resume_instance(id)`` → skips current node, continues BFS
```

## Data Flow: Variable Resolution

```
Template: "Hello {{lead.name}}, your company is {{company.name}}"

    1. TemplateRendererService.render(template)
    2. PATTERN finds {{lead.name}} and {{company.name}}
    3. For each match, calls resolver.resolve_path("lead.name")
    4. Resolver walks context["lead"]["name"] → "John Doe"
    5. Replaces placeholder → "Hello John Doe, your company is Acme Corp"
```

## Data Flow: Template Resolution (Sprint 18)

```
Flow Builder (PropertiesPanel.jsx)
    │
    ├── TemplateSelectField fetches GET /api/templates?channel=whatsapp|email
    └── Selected template's id stored as node.config.template_id

Execution (SendWhatsAppExecutor / SendEmailExecutor)
    │
    ├── node.config.template_id present?
    │     ├── yes → exec_ctx.template_service.get_template(template_id)
    │     │           → Template row (name/subject/content)
    │     │           → renderer.render(content) for {{variable}} substitution
    │     └── no  → legacy: renderer.render(node.config.template_name)  [backward compatible]
    │
    └── IntegrationFactory.get("whatsapp"|"email").execute(payload)

exec_ctx.template_service is a TemplateService(session) instance attached by the
engine at ExecutionContext construction — same pattern as resolver/renderer.
Executors never import TemplateService or query the database directly.
```

## Data Flow: Execution Monitor

```
JourneyMonitor.jsx  /  RunningInstances.jsx   (two callers, same drawer)
    │
    ├── runningInstanceService.list() → table rows
    ├── Auto-refresh every 10s
    ├── onRowClick → sets selectedId (JourneyMonitor also supports a `?instance=` deep link)
    │
    ▼
<ExecutionDrawer instanceId onClose onActionComplete />   (modules/journeys/ExecutionDrawer.jsx)
    │   self-fetches everything from just the id: runningInstanceService.get(),
    │   journeyService.get() (for the name), flowExecutionLogService.list(),
    │   approvalService.list(), taskService.list()
    │
    ├── Overview tab   (status, lead, current node, started/completed/duration)
    ├── Approvals tab  (shown only if status=waiting_approval or approvals exist — Approve/Reject buttons)
    ├── Tasks tab       (shown only if status=waiting_task or tasks exist — Complete/Reject buttons)
    ├── Steps tab       (node status indicators: green/blue/red/gray dots, from execution logs)
    ├── Timeline tab    (chronological execution-log entries with status badges — see note below)
    └── Raw JSON tab    (debug view)
```

This is the **execution/node timeline**, not a communication timeline: the
Timeline tab renders `FlowExecutionLog` rows (one "started" + one
"success"/"failed"/"skipped" per node), not domain-level communication
events ("WhatsApp Delivered", "Email Opened", etc.). No communication-event
timeline or Inbox UI exists in the codebase as of this writing — see
"Communication Architecture" below for what exists today and what a future
Communication Timeline would need.

`ExecutionDrawer.jsx` is the single shared drawer component — both
`JourneyMonitor.jsx` (global cross-journey monitor) and `RunningInstances.jsx`
(per-journey "Running" tab) render it identically. There is no separate
inline drawer implementation in either caller.

## Communication Architecture

There is exactly **one live path** that sends a real message, and **three
disconnected/dormant scaffolds** that look similar but are not on that path.
This distinction matters for anyone extending communication features (e.g. a
Communication Timeline/Inbox) — building on the wrong one silently does
nothing.

**Live path** (executor → integration → JAWIS):
```
SendWhatsAppExecutor / SendEmailExecutor   (app/execution/executors/)
    │  resolves template_id via exec_ctx.template_service, renders {{variables}}
    ▼
IntegrationFactory.get("whatsapp" | "email")     (app/integrations/factory.py)
    ▼
JawisWhatsAppIntegration / JawisEmailIntegration  (app/integrations/jawis_communication.py)
    │  POST {JAWIS_BASE_URL}/api/messages/{whatsapp,email}/send, Bearer JAWIS_API_TOKEN
    │  raises JawisCommunicationError on any failure (see ADR-017) — no {"success": False} swallowing
    ▼
provider_response returned verbatim, stored only in FlowExecutionLog.output
(no dedicated message/delivery table — see "Missing" below)
```

**Dormant/disconnected** (do not extend these without first re-reading this
section — none of them are reachable from any live request):
1. `app/communication/` — `CommunicationEngine` + mock `WhatsAppProvider`. Never instantiated. Predates the live path above.
2. `app/providers/` — `ProviderRegistry`/`Channel`/`MetaProvider`/`ResendProvider`. Never imported by the live app; its `ResendProvider` import is currently broken (missing file — `KNOWN_ISSUES.md` #8). This is the intended extension point for real Meta Cloud API / Resend support (`docs/roadmap.md` Sprint 22), but needs to be either wired into `IntegrationFactory` or replaced by new `integrations/` classes following the existing `Jawis*Integration` pattern — not extended in isolation.
3. `Conversation`/`Message` SQLAlchemy models (`app/models/conversation.py`, `message.py`) — defined but **not registered** in `app/models/__init__.py`, so not part of `Base.metadata` and not created by any migration the live app runs. A two-table (conversation + message) design, which would conflict with any future single-event-model requirement for a communication timeline.

**What's missing for a Communication Timeline / Inbox** (not yet built, no
code exists for any of this — flagged here purely so future work knows the
actual starting point): a single communication-event model distinct from
`FlowExecutionLog`; a hook inside `ExecutionEngine._execute_node()` (the one
choke-point every node already passes through) to emit that event; and an
inbound status-callback route for delivery/read/reply receipts, since
nothing in the app currently ingests those from any provider.

## Running Instance Lifecycle

`RunningJourneyInstance.status` (`app/models/running_journey_instance.py`,
`InstanceStatus` enum) has six values. All transitions go through
`RunningInstanceService` (`app/services/running_instance_service.py`),
called only from `ExecutionEngine` — nothing else mutates instance status.

```
   (created) ──► running ──► completed        (End node reached)
                    │
                    ├──► failed                (executor raised, or returned success=False)
                    │
                    ├──► waiting               (Wait node — resumed by SchedulerService
                    │                           polling resume_at, or manual resume_instance())
                    │
                    ├──► waiting_approval      (Approval node — resumed by
                    │                           POST /api/approvals/.../approve|reject)
                    │
                    └──► waiting_task          (ManualTask node — resumed by
                                                 POST /api/tasks/.../complete|reject)

   failed ──(retry_node / retry_journey, user-triggered only)──► running
```

Notes:
- **Delay** nodes do *not* produce a distinct status — they store `resume_at` in `instance.data` but the instance stays `running` (only a Wait node changes status to `waiting`). Both are resumed the same way (`SchedulerService` polling), but only Wait nodes change status.
- `waiting`/`waiting_approval`/`waiting_task` all resume through the same `ExecutionEngine.resume_instance()` → `_resume_from(skip_current=True)` path — the paused node is skipped, traversal continues from its neighbours (ADR-014).
- `retry_node`/`retry_journey` are user-triggered only (`POST /running-instances/{id}/retry?mode=`), never automatic — there is no automatic retry on failure (ADR-017).
- No `pending`, `paused`, or `cancelled` states exist in the implementation, despite being proposed in the archived root `ARCHITECTURE.md` (§10) — the six states above are the actual, current set.
- All state is carried in `instance.data` (JSON column) — `current_node_id`, `resume_at`, `retry_count`, `approvals`, `tasks` — per ADR-010 (no schema changes).

## Future Extension Points

1. ~~**Scheduler** — pause/resume engine at Wait/Delay nodes~~ ✅ Sprint 8+9
2. ~~**Retry Engine** — retry failed nodes with backoff~~ ✅ Sprint 8+9
3. ~~**Integration Layer** — BaseIntegration + factory + WhatsApp/Email/Notification integrations~~ ✅ Sprint 10+11
4. ~~**JAWIS LeadProvider** — replace DummyLeadProvider with live JAWIS data~~ ✅ Sprint 16+17
5. ~~**JAWIS CRM Integration** — CRM actions against real JAWIS API~~ ✅ Sprint 16+17
6. ~~**Template Management** — single `Template` model, `/api/templates` CRUD, Flow Builder template selector, `template_id` resolution in execution~~ ✅ Sprint 18
7. ~~**Journey Dashboard** — per-journey Execution Metrics/Flow Summary/Trigger Mapping/Integration Status, `GET /api/integrations/health`~~ ✅ Sprint 19
8. **Real Meta WhatsApp API** — replace simulated WhatsAppIntegration
9. **AI Conditions** — AI-powered condition evaluation
10. **Variable Filters** — `{{upper(lead.name)}}`, `{{date(today)}}`
11. **Cross-Journey Analytics** — org-wide trends/comparisons across journeys (per-journey metrics already covered by Sprint 19)

## Key Design Constraints

- No database schema changes after initial setup, **except** narrow, additive
  changes to bring an already-existing table in line with a model that's
  actually used (e.g. Sprint 18 made `templates.workspace_id` nullable because
  nothing populates it yet — no new tables, no destructive changes)
- No WebSockets (polling only)
- All node configuration stored inside Flow Definition JSON (`node.config`)
- New node type = 1 executor file + 1 factory registration
- Lead/Company data fetched via provider interface (not direct DB queries)
- Scheduler runs as in-process asyncio task (no Redis/Celery)
- Retry count stored in instance.data JSON (no separate column)

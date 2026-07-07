# JAWCOM — Architecture

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
| `events/` | Event types and handlers | services/ |
| `jawis/` | JAWIS API client (external system) | config/ |
| `flows/` | Flow builder/manager (legacy — still constructs the old sync `TemplateService(Session)`, unused) | — |
| `journeys/` | Journey manager (legacy) | — |
| `stage_mapping/` | Stage mapping manager (legacy) | — |
| `runtime/` | Running instance schemas/validators | models/ |
| `config/` | Settings, logging | — |
| `database/` | Session management, base model | — |
| `core/` | Base repository, dependencies | database/ |
| `providers/` | External communication providers (future) | — |

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
JourneyMonitor.jsx
    │
    ├── runningInstanceService.list() → table rows
    ├── onRowClick → runningInstanceService.get(id) + flowExecutionLogService.list()
    ├── Auto-refresh every 10s
    │
    └── Sheet (right drawer)
          ├── Overview tab (status, lead, current node, started/completed/duration)
          ├── Steps tab (node status indicators: green/blue/red/gray dots)
          ├── Timeline tab (chronological log entries with status badges)
          └── Raw JSON tab (debug view)
```

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

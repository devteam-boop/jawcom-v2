# JAWCOM — Module Dependencies

## Dependency Graph

```
┌─────────────────────────────────────────────────────────────────────┐
│                         api/ (routes)                               │
│  journey_routes  flow_definition_routes  execution_routes           │
│  running_instance_routes  flow_execution_log_routes                 │
│  stage_mapping_routes  flow_version_routes  template_routes         │
└───────────────────────┬─────────────────────────────────────────────┘
                        │ depends on
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      services/ (business logic)                      │
│  journey_service  flow_definition_service  running_instance_service  │
│  flow_execution_log_service  flow_version_service                   │
│  stage_mapping_service  flow_validation_service                      │
│  variable_resolver_service  template_renderer_service                │
│  wait_scheduler_service  retry_service  approval_service  task_service│
└───────┬─────────────────────────────────┬───────────────────────────┘
        │ depends on                      │ depends on
        ▼                                 ▼
┌───────────────┐               ┌─────────────────────┐
│ repositories/ │               │    execution/        │
│ (data access) │               │ engine.py            │
└───────┬───────┘               │ executors/           │
        │                       │ providers/           │
        ▼                       └──────────┬──────────┘
┌─────────────────┐                       │
│   models/        │                       │ delegates to
│ (SQLAlchemy ORM) │                       ▼
└─────────────────┘               ┌─────────────────────┐
                                   │  integrations/       │
                                   │  base.py             │
                                   │  factory.py          │
                                   │  config.py           │
                                   │  whatsapp.py         │
                                   │  email.py            │
                                   │  notification.py     │
                                   │  crm.py (DummyCRM)   │
                                   │  jawis_crm.py        │
                                   └─────────────────────┘
                                          │
                                          ▼
                                  ┌─────────────────────┐
                                  │ services/            │
                                  │ variable_resolver    │
                                  │ template_renderer    │
                                  └─────────────────────┘
                                          │
                                          ▼
                                  ┌─────────────────────┐
                                  │ execution/providers/ │
                                  │ LeadProviderFactory  │
                                  │ DummyLeadProvider    │
                                  │ JawisLeadProvider    │
                                  └─────────────────────┘

events/ (inbound webhook → typed event → dispatch)
  api/main.py (POST /api/webhooks/jawis) ──► jawis/webhook.py (normalize_jawis_payload)
                                                  │
                                                  ▼
                                          events/event_types.py (create_event_from_type)
                                                  │
                                                  ▼
                                          events/dispatcher.py (EventDispatcher.dispatch)
                                                  │
                                                  ▼
                                          events/handlers.py (CommunicationEventHandler)
                                                  │ constructs ExecutionEngine directly
                                                  ▼
                                          execution/engine.py (handle_lead_created / handle_lead_stage_changed)

  Handler registration happens once at FastAPI startup (main.py), not per-request.

Dormant modules — not part of any dependency chain above, not imported by
live code, do not extend without first reading `architecture.md`'s
"Communication Architecture" section:
  app/communication/  (CommunicationEngine — never instantiated)
  app/providers/       (ProviderRegistry/MetaProvider/ResendProvider — never imported;
                         ResendProvider's target file doesn't exist on disk)

templates/ (Sprint 18 — same layer as services/, own top-level package)
  api/template_routes.py ──► templates/services.py (TemplateService)
                                  │ depends on
                                  ▼
                          repositories/template_repository.py ──► models/template.py (Template)

  execution/engine.py constructs TemplateService(session) and attaches it to
  ExecutionContext.template_service; executors call it, never import it directly
  (same pattern as resolver/renderer — see execution/executors/base.py)
```

## Allowed Dependencies

| Module | Can Import | Cannot Import |
|---|---|---|
| `api/` | services/, schemas/ | repositories/, models/, execution/ |
| `services/` | repositories/, models/ | api/, execution/engine (except scheduler/retry services which may construct engine) |
| `repositories/` | models/ | api/, services/ |
| `models/` | database/ (base) | api/, services/, repositories/ |
| `execution/engine.py` | services/, models/, execution/executors/, execution/providers/, `app/templates/` | api/ |
| `execution/executors/` | execution/executors/base.py, app/integrations/ | services/, models/, repositories/, api/, `app/templates/` |
| `integrations/` | config/ (settings) | services/, models/, repositories/, api/, execution/ |
| `execution/providers/` | (stdlib only) | services/, models/, api/ |
| `events/` | `execution/` (`CommunicationEventHandler` constructs `ExecutionEngine` directly) | api/, repositories/, models/ |
| `jawis/` | config/, `events/` (`webhook.py` dispatches through `EventDispatcher`) | services/, repositories/, models/ |
| `templates/` | repositories/, models/ | api/, execution/ (only the engine imports `templates/`; executors receive a `TemplateService` instance via `exec_ctx.template_service`, never import `templates/` directly) |

## Forbidden Dependencies

- ❌ `api/` → `repositories/` (routes never call repositories directly)
- ❌ `api/` → `execution/engine.py` (routes use services)
- ❌ `services/` → `api/` (services don't know about routes)
- ❌ `execution/executors/` → `services/` (executors don't call business services)
- ❌ `execution/executors/` → `repositories/` (executors don't access data layer)
- ❌ `execution/executors/` → `models/` (executors receive data, not models)
- ❌ `execution/providers/` → `services/` or `models/` or `repositories/`
- ❌ `execution/executors/` → external APIs directly (delegate to integrations)
- ❌ `integrations/` → `execution/` or `services/` or `models/` (integrations are leaf adapters)
- ❌ `jawis/` → `execution/` (JAWIS is an external system adapter)

## Key Dependency Rules

1. **Services are the hub** — all business logic flows through services. Routes call services, services call repositories.

2. **Executors are leaf nodes** — they depend only on `base.py` and `integrations/` and receive everything they need via parameters.

3. **Providers are leaf nodes** — `LeadProvider` interface has no dependencies beyond stdlib. Implementations may depend on external clients (e.g., JawisClient).

4. **Engine is the orchestrator** — it depends on services (for DB), executors (for node logic), and providers (for data). Nothing depends on the engine.

5. **No circular imports** — the dependency graph must remain a DAG. If A depends on B, B must not depend on A.

6. **Legacy modules** (`flows/`, `journeys/`, `stage_mapping/`) — should not be imported by new code. They exist for backward compatibility and should be phased out.

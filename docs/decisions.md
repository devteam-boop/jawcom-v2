# JAWCOM — Architecture Decision Records

## ADR-001: Executor Framework (Instead of If-Else Chain)

**Status:** Accepted
**Context:** The engine originally used an if-else chain to handle different node types. Adding a new node type required modifying the engine.

**Decision:** Extract node logic into individual executor classes registered via `ExecutorFactory`. The engine dispatches by node type string and never contains node-specific logic.

**Consequences:**
- ✅ Adding a new node type = 1 file + 1 factory registration
- ✅ Engine stays stable regardless of how many node types exist
- ✅ Each executor is independently testable
- ❌ Slight indirection overhead

## ADR-002: Factory Pattern for Providers

**Status:** Accepted
**Context:** The engine hardcoded `DummyLeadProvider()`. Switching to a real provider (JAWIS, CRM) required engine modification.

**Decision:** Create `LeadProviderFactory` with a registry. Engine calls `LeadProviderFactory.get_provider("dummy")`. New providers are registered without touching the engine.

**Consequences:**
- ✅ Zero engine changes when adding providers
- ✅ Configuration-driven provider selection (future)
- ✅ Testable with mock providers

## ADR-003: Variable Resolution vs Template Rendering Separation

**Status:** Accepted
**Context:** `VariableResolverService` handled both `{{...}}` pattern matching and dotted-path lookup. Adding future features like filters (`{{upper(lead.name)}}`) would make the class complex.

**Decision:** Split into `VariableResolverService` (path lookup only) and `TemplateRendererService` (pattern matching + delegate to resolver).

**Consequences:**
- ✅ Filters can be added to the renderer without touching the resolver
- ✅ Clearer responsibility boundaries
- ✅ Renderer is future-ready for `{{upper(...)}}`, `{{date(...)}}`

## ADR-004: ExecutionContext Dataclass

**Status:** Accepted
**Context:** Executors received raw `node`, `running_instance`, `lead_id`, `context` params. Accessing lead/company data required ad-hoc fetching.

**Decision:** Create a rich `ExecutionContext` dataclass containing resolved lead/company data, journey metadata, resolver, renderer, and node outputs.

**Consequences:**
- ✅ Executors have everything they need in one object
- ✅ No ad-hoc data fetching in executors
- ✅ Node outputs automatically available for downstream variable resolution
- ✅ ExecutionContext is a dataclass (JSON-serializable-friendly)

## ADR-005: BFS Traversal (Instead of next_node_id)

**Status:** Accepted
**Context:** The original design used `result.next_node_id` from each executor to determine the next node. This created tight coupling between executors and graph structure.

**Decision:** The engine builds an adjacency list from `definition["edges"]` and uses BFS traversal. Executors no longer control flow routing (except ConditionExecutor which sets `true_next_node_id`/`false_next_node_id` in config).

**Consequences:**
- ✅ Engine fully controls traversal
- ✅ Executors don't need to know about graph structure
- ✅ ConditionExecutor stores branch targets in config (not in result)
- ✅ Hardcoded `if node_type == "end"` in engine is acceptable for traversal termination

## ADR-006: Stage Mapping (Instead of Journey Trigger)

**Status:** Accepted
**Context:** The `journey.trigger_value` field was originally meant to link journeys to stages. Multiple journeys could match the same stage event.

**Decision:** Create a separate `stage_mappings` table that links `stage_key` to `journey_id`. The engine queries stage mappings to find matching journeys.

**Consequences:**
- ✅ Multiple journeys can trigger from the same stage event
- ✅ Clean many-to-many relationship
- ✅ Stage mappings are independently manageable
- ✅ `journey.trigger_value` is legacy (not read by engine)

## ADR-007: No WebSockets (Polling Only)

**Status:** Accepted
**Context:** Real-time updates for the Execution Monitor.

**Decision:** Use 10-second polling `setInterval` instead of WebSockets.

**Consequences:**
- ✅ Simpler implementation
- ✅ No special server infrastructure needed
- ✅ No connection management overhead
- ❌ Up to 10-second delay in updates
- ❌ Slightly more network requests

## ADR-008: Config Inside Flow JSON (No Separate Tables)

**Status:** Accepted
**Context:** Node configuration (template names, durations, conditions) needed storage.

**Decision:** Store all node config inside the Flow Definition JSON (`node.config` key). No separate database tables for node configuration.

**Consequences:**
- ✅ No schema migrations for new node types
- ✅ Config travels with the flow (export/import ready)
- ✅ Single source of truth
- ❌ Nested JSON can be harder to query directly (not needed for execution)

## ADR-009: Engine Creates Logs (Not Executors)

**Status:** Accepted
**Context:** Executors originally created their own execution logs via `build_log_payload()`. This duplicated logging logic.

**Decision:** The engine creates all execution logs ("started" and "success"/"failed"). Executors return `ExecutionResult` with output data. The engine stores the output in the log.

**Consequences:**
- ✅ Consistent log format across all node types
- ✅ Executors don't need to know about logging
- ✅ Engine controls error handling and instance state
- ❌ `build_log_payload()` in utils.py is now dead code (should be removed in cleanup sprint)

## ADR-010: No Database Schema Changes

**Status:** Accepted
**Context:** Each new feature could require new columns/tables.

**Decision:** Use the existing `data` JSON column on `RunningJourneyInstance` for any new fields. No new database migrations.

**Consequences:**
- ✅ Zero schema migration risk
- ✅ Schema-independent feature development
- ❌ JSON columns are not type-enforced by the database (enforced at application level)

## ADR-011: Poll-Based In-Process Scheduler (No Redis/Celery)

**Status:** Accepted
**Context:** Wait and Delay nodes need a scheduler to resume paused instances. The project has no Redis, Celery, or external task queue.

**Decision:** Implement `SchedulerService` as a background `asyncio.create_task` inside the FastAPI process. It polls every 30 seconds for instances with `status="waiting"` and `data.resume_at <= now`, then calls `engine.resume_instance()`.

**Consequences:**
- ✅ Zero infrastructure dependencies (no Redis, no Celery)
- ✅ Simple implementation (single file, no config)
- ✅ Graceful shutdown via task cancellation
- ❌ Scheduler runs in the same process as the API (if the app restarts, polling resumes within 30s)
- ❌ No persistence of scheduled wake-ups across app restarts
- ❌ Not horizontally scalable without extracting to a separate service

## ADR-012: Skip-Status (Not next_node_id) for Pause Flow

**Status:** Accepted
**Context:** Wait and Delay nodes needed a way to signal "execution succeeded but traversal should stop." Using `result.next_node_id=None` would conflict with end-of-flow semantics. Using a separate status field avoided overloading existing fields.

**Decision:** Wait/Delay executors return `ExecutionResult(success=True, status="skipped", updated_context={"resume_at": ..., "_wait": ...})`. The engine checks `result.status == "skipped"` to determine that traversal should stop, reads `resume_at` from the context, and transitions instance state accordingly.

**Consequences:**
- ✅ Clearer semantics than overloading `next_node_id`
- ✅ `status="skipped"` is already defined in `ExecutionResult` docstring
- ✅ Future node types can also use "skipped" for conditional bypass
- ❌ Engine has a third non-traversal path (success + skipped), adding complexity to `_execute_node`

## ADR-013: Integration Layer (Not Inline API Calls in Executors)

**Status:** Accepted
**Context:** Action executors (SendWhatsApp, SendEmail, Notification) built payloads and logged them internally. Adding real API calls would have required modifying each executor, and there was no standard interface for external service adapters.

**Decision:** Introduce an `app/integrations/` package with:
- `BaseIntegration` ABC defining `connect()`, `disconnect()`, `health()`, `execute()`
- `IntegrationFactory` registry (same pattern as `LeadProviderFactory` and `ExecutorFactory`)
- Concrete integrations that implement `execute()` for each service
- Executors build request payloads and delegate to `IntegrationFactory.get(name).execute(payload)`

**Consequences:**
- ✅ Adding a new external service = 1 integration file + 1 factory registration — executors unchanged
- ✅ Executors never call external APIs directly (enforced by architecture)
- ✅ Consistent health check framework across all integrations
- ✅ IntegrationConfig centralizes all secrets (no hardcoded credentials)
- ❌ Extra indirection layer for simulated integrations (acceptable for consistency)
- ❌ Integration package could grow large as more providers are added (mitigated by file-per-integration layout)

## ADR-014: Halt-Pause Pattern (Instead of Resume-At) for Human Interactions

**Status:** Accepted
**Context:** Approval and Manual Task nodes need to pause journey execution until a human completes an action. Unlike Wait/Delay nodes (which have a known resume time), human-triggered pauses have no predictable duration and no timer.

**Decision:** Reuse the existing `status="skipped"` mechanism but add a `_halt` key in `updated_context` to discriminate pause reasons:
- `_halt=approval` → engine calls `instance_service.wait_approval()`, status becomes `waiting_approval`
- `_halt=task` → engine calls `instance_service.wait_task()`, status becomes `waiting_task`
- `_halt` absent but `resume_at` present → existing Wait/Delay behavior
- `_halt` absent and `resume_at` absent → plain skip (no status change)

Approval and Task data (ID, title, description, status) is stored in `instance.data.approvals` and `instance.data.tasks` JSON objects — no new tables.

Resume uses the existing `engine.resume_instance()` path — the node is skipped and traversal continues to downstream neighbours.

**Consequences:**
- ✅ Zero schema changes (approvals/tasks live in JSON column)
- ✅ Zero engine architecture changes (extended existing skipped handler)
- ✅ Reuses existing resume/retry framework
- ✅ No new tables (follows ADR-010: No Database Schema Changes)
- ❌ Approvals/tasks not queryable across instances without scanning all data (acceptable for current scale)
- ❌ No timeout auto-enforcement (future sprint can add scheduler support)
- ❌ No notifications for pending approvals/tasks (future sprint)

## ADR-015: Env-Var-Controlled Provider Switching

**Status:** Accepted
**Context:** The system used `DummyLeadProvider` and `DummyCRMIntegration` for development/testing. To use live JAWIS data, the engine and executors would need to be aware of which provider is active, violating the factory-pattern isolation.

**Decision:** Instead of modifying the engine or executors, control provider selection through environment variables at the factory level:

1. `LeadProviderFactory.get_provider()` reads `JAWIS_LEAD_PROVIDER` env var (default `"dummy"`) to select which provider class to instantiate
2. `IntegrationFactory` now supports `register_alias()` — the `"crm"` alias resolves to either `"crm_dummy"` or `"crm_jawis"` based on `JAWIS_CRM_PROVIDER` (default `"dummy"`)
3. Engine and executors continue to call `LeadProviderFactory.get_provider()` and `IntegrationFactory.get("crm")` with no changes
4. The alias resolution happens at module import time — env var must be set before app startup

**Consequences:**
- ✅ Zero engine/executor code changes — all switching happens in factories
- ✅ `DummyLeadProvider`/`DummyCRMIntegration` remain the default — no risk of accidentally hitting production JAWIS
- ✅ Both backends (dummy and jawis) are registered simultaneously — explicit calls to `get_provider("dummy")` or `IntegrationFactory.get("crm_dummy")` bypass the env var
- ✅ Follows existing factory pattern (ADR-002)
- ❌ Env var must be set before app startup (module-level alias resolution has no runtime switching) — acceptable for deployment-phase configuration
- ❌ Adds a level of indirection via aliases that may confuse new developers — documented in factory docstring

## ADR-016: Single Template Model (`Template`, Not `CustomTemplate`)

**Status:** Accepted
**Context:** Two competing template models existed: `Template` (`templates` table, migrated, workspace-scoped, FK target of the dormant `Campaign`/`Message` cluster and of the live `stage_mappings.template_id` column) and `CustomTemplate` (`custom_templates` table, never migrated — the table didn't exist — but backed by a fully-implemented `TemplateService`). Both were dead ends: `Template` had no service; `CustomTemplate` had no table.

**Decision:** Consolidate on `Template`/`templates`. Port the existing `TemplateService`/`TemplateValidator`/`TemplateRenderer` logic onto it (rewriting the service to async in the process — see below), delete `CustomTemplate` and its model file, and never create `custom_templates`.

Activating `Template` required decoupling it from the dormant Workspace/Campaign/Message scaffold: that cluster's modules are never imported anywhere in the app, and `Journey` has no matching side of `Workspace.journeys`. Declaring `Template.workspace = relationship("Workspace", ...)` crashes `configure_mappers()`; keeping even a bare `ForeignKey('workspaces.id')` on the column crashes at flush time with `NoReferencedTableError` (the `workspaces` table is never registered in `Base.metadata`). `templates.workspace_id` is now a plain nullable UUID column with no Python-level FK or relationship — the physical DB-level FK constraint from the initial migration is untouched, so workspace scoping can be re-enabled later with zero further schema changes.

**Consequences:**
- ✅ Zero data migration — `custom_templates` never had a table, so there was nothing to migrate away from
- ✅ Reuses the `stage_mappings.template_id` FK and the `Campaign.template_id`/`Message.template_id` FK targets that already point at `templates.id`
- ✅ `Template.channel`/`Template.status` enums map directly onto the Templates page's channel folders and status badges
- ✅ `TemplateService` now follows the same async `AsyncSession` + Repository pattern as every other service (it previously used a synchronous `Session` and raw `.query()` calls)
- ❌ `app/flows/services.py`/`validators.py` (already-legacy, unreferenced) and `app/communication/engine.py` (never instantiated) still construct `TemplateService` with the old synchronous signature — left as-is since nothing calls them; will need updating if that dormant code is ever revived
- ❌ Workspace scoping is not actually enforced anywhere yet — `workspace_id` is a nullable column with no application-level population until multi-tenancy (Sprint 23 candidate) is built

## ADR-017: JAWIS Communication Integration Raises Instead of Returning `{"success": False}`

**Status:** Accepted
**Context:** `JawisCRMIntegration` (ADR-013's pattern) catches API failures internally and returns `{"success": False, "error": ..., ...}` from `execute()`. Every executor, however, always builds `ExecutionResult(success=True, ...)` regardless of what `integration.execute()` returns — the `success` key inside `provider_response` is stored for observability but never actually checked. This means a CRM failure never surfaces as a failed node/instance today. The task required "if JAWIS unavailable, mark execution failed, do not retry" for the new WhatsApp/Email integrations, but explicitly forbade touching executors or the engine.

**Decision:** `JawisCommunicationIntegration.execute()` (`app/integrations/jawis_communication.py`) raises `JawisCommunicationError` on any failure — missing configuration, unreachable host, non-2xx response — instead of returning a `{"success": False}` dict. The uncaught exception propagates out of `SendWhatsAppExecutor`/`SendEmailExecutor` (neither wraps the `integration.execute()` call in a try/except) into the engine's existing `_execute_node()` handler, which already creates a failed `FlowExecutionLog` and calls `instance_service.fail()` on any executor exception — a mechanism that already existed and required no changes.

**Consequences:**
- ✅ "JAWIS unavailable → failed node, no retry" works correctly with zero executor or engine changes
- ✅ On success, the JAWIS response dict is returned and stored as `provider_response` exactly as received — no wrapping, no key renaming
- ❌ This is now inconsistent with `JawisCRMIntegration`'s catch-and-return convention — two different error-handling styles exist in the integration layer. Reconciling them (e.g., making all integrations raise, and updating every executor to check `integration_response["success"]`) is a fair follow-up but was out of scope (would require executor changes, explicitly forbidden by this task)
- ❌ Since `RetryService.retry_node()`/`retry_journey()` are user/manually-triggered (via `POST /running-instances/{id}/retry`), "do not retry" simply means no *automatic* retry occurs — a user can still manually retry a failed node afterward, same as any other failed node

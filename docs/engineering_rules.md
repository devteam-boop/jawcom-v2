# JAWCOM — Engineering Rules

These are **permanent project laws**. Every sprint, every implementation, every refactor must obey them. Violations must be treated as bugs.

## Architecture Rules

1. **Execution Engine never contains node business logic.** The engine orchestrates traversal, logging, and instance state — it never implements behaviour for a specific node type.

2. **Executors contain only single-node logic.** Each executor implements exactly one node type. It never handles traversal, logging, or instance state.

3. **Validation never executes nodes.** `FlowValidationService` performs static graph analysis and node config checks only. It never calls `ExecutorFactory` or `_execute_node`.

4. **Execution Engine never calls external APIs.** The engine does not call WhatsApp, SMTP, or any external service. That responsibility belongs to individual executors (and even they only simulate in the current sprint).

5. **Always use Factory pattern for providers.** `LeadProviderFactory` is the sole way to obtain a provider instance. Never call `DummyLeadProvider()` or any concrete provider constructor directly in the engine or executors.

6. **Never instantiate providers directly.** The engine must never know which concrete `LeadProvider` is in use. Only `LeadProviderFactory` knows the registry.

7. **Never duplicate configuration.** All node configuration lives exclusively inside the Flow Definition JSON (`node.config`). No separate config tables, no hardcoded defaults in executors.

8. **Variable resolution is separate from template rendering.** `VariableResolverService` resolves dotted paths (`lead.name` → `"John"`). `TemplateRendererService` handles `{{...}}` pattern matching and delegates path lookup to the resolver. They are not the same service.

## Layer Rules

9. **Routes never contain business logic.** FastAPI route handlers only parse requests, call services, and return responses.

10. **Repositories never called directly from routes.** Only Service classes access repositories.

11. **Only Services access repositories.** `Repository` classes are the single data-access layer. No other module calls them.

12. **Services never call other Services directly for data access.** If Service A needs data from Service B, it goes through the repository layer.

## Frontend Rules

13. **No UI redesigns without explicit request.** Enhance existing components; never rewrite pages from scratch.

14. **No WebSockets.** Use polling (10-second intervals) for real-time updates.

15. **No new database tables.** Work with existing models and the `data` JSON column on `RunningJourneyInstance`.

## Node Type Addition Rules

16. Adding a new node type requires exactly:
    - One executor file in `backend/app/execution/executors/<type>_executor.py`
    - One registration in `ExecutorFactory._executors` dict
    - Nothing else.

17. Adding a new node type does NOT require changes to:
    - The engine
    - The database schema
    - The frontend Flow Builder (if it uses generic config form)
    - The validation service

## Data Rules

18. All lead/company runtime data comes through `LeadProvider`. No direct DB queries for lead or company data.

19. `current_node_id`, `resume_at`, `retry_count`, and all execution metadata are stored in `RunningJourneyInstance.data` JSON column — not as separate columns.

20. `FlowExecutionLog` records one "started" and one "success|failed|skipped" entry per node execution.

## Scheduler & Retry Rules

21. `SchedulerService` is the only component that polls for waiting instances. No other module queries by `status="waiting"` for resumption.

22. `RetryService` enforces the retry policy (`max_retries`, `retry_delays`) from `instance.data.retry_policy`. The engine does not enforce retry limits — it only provides the execution mechanism.

23. Resume and retry go through the engine's `_resume_from()` method, not through `_execute_for_stage()`. This ensures the existing instance is reused (not a new instance created).

## Human Task & Approval Rules

24. **Approval and Manual Task nodes use `_halt` in `updated_context`** to signal pause reason to the engine. `_halt=approval` transitions instance to `waiting_approval`. `_halt=task` transitions to `waiting_task`. No engine architecture changes needed.

25. **Approval and Task data is stored exclusively in `instance.data` JSON columns** — `approvals` and `tasks` dicts. No new database tables. No schema changes.

26. **Resume after approval/task completion** goes through the same `engine.resume_instance()` path as Wait/Delay nodes. The completed node is skipped and traversal continues to downstream neighbours.

27. **Executors never call ApprovalService or TaskService.** Executors build the approval/task data and return it in `updated_context`. The engine stores it in `instance.data`. Services are only called by API routes.

## Provider Rules

24. **LeadProviderFactory.get_provider() must never be called with a hardcoded name in engine or executor code.** Always call `LeadProviderFactory.get_provider()` (no argument) to let the env var determine the backend. Explicit names like `get_provider("dummy")` are only for tests or debugging.

25. **JAWIS_LEAD_PROVIDER env var controls which provider is active.** Set to `"jawis"` for live JAWIS data, `"dummy"` (default) for simulated data. Must be set before app startup.

26. **JawisLeadProvider wraps JawisClient — no other code calls JawisClient directly.** The provider interface is the single entrypoint for lead/company data.

## Integration Rules

27. **Executors never call external APIs directly.** All external communication goes through `IntegrationFactory.get(name).execute(payload)`.

25. **Every external service has exactly one integration file** in `app/integrations/`. No ad-hoc API calls in executors, services, or routes.

26. **IntegrationFactory is the only way to obtain an integration instance.** Never instantiate `WhatsAppIntegration()` or any concrete integration constructor directly.

27. **All secrets live in environment variables** loaded through `Settings` and accessed via `IntegrationConfig`. No hardcoded API keys, tokens, or credentials anywhere in the codebase.

28. **Integrations are leaf adapters** — they depend only on `base.py` and `config.py`. They never import from `execution/`, `services/`, `models/`, or `repositories/`.

29. **Adding a new external service requires exactly:**
    - One integration file in `app/integrations/<name>.py`
    - One registration in `app/integrations/__init__.py`
    - Integration settings in `app/config/settings.py` (if secrets needed)
    - Nothing else (no executor changes, no engine changes)

30. **Never call `IntegrationFactory.get("crm_jawis")` or `IntegrationFactory.get("crm_dummy")` directly in executors or engine code.** Always use `IntegrationFactory.get("crm")` which resolves to the correct backend via the `JAWIS_CRM_PROVIDER` env var alias.

31. **The `"crm"` alias is registered at module import time.** If you need to change the CRM backend at runtime, you must restart the application; the alias cannot be changed mid-execution.

32. **Both CRM backends are always registered.** You can always call `IntegrationFactory.get("crm_dummy")` explicitly (e.g., for testing) regardless of the `JAWIS_CRM_PROVIDER` setting.

## Template Rules

33. **`Template` (`templates` table) is the only template model.** Never introduce a second template table or model. Adding template-related fields means altering `Template`/`templates`, not creating a parallel table.

34. **Executors never import `app/templates/` or query the database for a template directly.** Template resolution goes through `exec_ctx.template_service` (a `TemplateService` instance the engine attaches to `ExecutionContext` at construction, the same way `resolver`/`renderer` are attached). Executors only call `await exec_ctx.template_service.get_template(template_id)`.

35. **`node.config.template_id` is the canonical way a flow node references a template.** The legacy free-text `node.config.template_name` is read only as a fallback when `template_id` is absent — for backward compatibility with flows saved before Sprint 18, not as an alternative going forward.

## Prohibited Patterns

- ❌ Engine calling WhatsApp/SMTP API directly
- ❌ Service importing another service's repository
- ❌ Route importing a repository
- ❌ Executor accessing database directly
- ❌ Hardcoding provider instances
- ❌ Duplicating node config outside Flow JSON
- ❌ Synchronous database calls in async context
- ❌ Using WebSockets instead of polling
- ❌ Schema migrations for new features (use JSON columns) — narrow, additive migrations to an existing table already in use (e.g. relaxing a stale NOT NULL) are the sole exception; see ADR-016
- ❌ A second template model/table alongside `Template`/`templates`

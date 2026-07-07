# JAWCOM — AI Context

## Vision
A configurable journey automation platform. Business events (lead stage changes) trigger flow execution. Flows are built visually via ReactFlow, validated, published, then executed by a pluggable executor engine.

## Current Architecture (high-level)

```
Webhook / Test Call → Stage Mapping → Journey → Flow Definition
    → Validation → Execution Engine → Executor Factory → Executors
                                          │
                                    IntegrationFactory
                                          │
                               ┌───────────┼───────────┬──────────┬──────────────┐
                               ▼           ▼           ▼          ▼              ▼
                       WhatsApp    Email    Notification    CRM (dummy)      CRM (JAWIS)
                       (simulated) (simulated) (simulated) (simulated)  (live API calls)
    → Running Instance → Execution Logs → Execution Monitor
                                         ↓
                                   SchedulerService
                                         ↓
                                   RetryService
                                         ↓
                              ApprovalService / TaskService
```

**Key components:**
- **Stage Mapping** — links a JAWIS stage key to a journey
- **Flow Definition** — JSON graph of nodes+edges built in ReactFlow
- **Execution Engine** — BFS traversal dispatching each node to its executor
- **Executor Factory** — registry of `{node_type: executor_class}` (16 executors)
- **Integration Layer** — `BaseIntegration` interface, `IntegrationFactory` registry with alias support, 5 integrations (whatsapp, email, notification, crm_dummy, crm_jawis); `"crm"` alias resolved by `JAWIS_CRM_PROVIDER` env var
- **Variable Resolver** — resolves `{{lead.name}}` from runtime context
- **Template Renderer** — separates `{{...}}` pattern replacement from variable lookup
- **Lead Provider Factory** — registry-based provider; default `DummyLeadProvider` or `JawisLeadProvider` (env-var-switchable)
- **Execution Context** — rich context object passed to every executor
- **SchedulerService** — background asyncio task, polls waiting instances every 30s
- **RetryService** — node-level and journey-level retry with configurable policy
- **Execution Monitor** — React dashboard with detail drawer, timeline, auto-refresh

## Current Sprint
Sprint 16+17 — JAWIS Live Integration (completed)

## Next Sprint
TBD (Variable Filters, AI Conditions, Real WhatsApp API, etc.)

## Golden Rules
1. Engine never contains node business logic (only traversal + logging)
2. Executors contain only single-node logic
3. Validation never executes nodes
4. Engine never calls WhatsApp/SMTP directly
5. Always use Factory pattern for providers
6. Never instantiate providers directly (use LeadProviderFactory)
7. Node config lives only inside Flow Definition JSON
8. Variable resolution is separate from template rendering
9. Routes never contain business logic
10. Only Services access repositories
11. New node type = executor file + factory registration — nothing else
12. SchedulerService is the only poller for waiting instances
13. Resume/retry go through engine._resume_from(), not _execute_for_stage()
14. Executors delegate to IntegrationFactory for all external communication
15. IntegrationFactory is the only way to get an integration (never instantiate directly)
16. Approval/Task executors use `_halt` in updated_context — never call services directly
17. Approval/Task data lives in instance.data JSON — no new tables
18. Resume after approval/task goes through the same engine.resume_instance() path
19. Provider switching is done by env var at the factory level — never in engine or executors
20. JAWIS_LEAD_PROVIDER=dummy|jawis controls which LeadProvider is returned by LeadProviderFactory
21. JAWIS_CRM_PROVIDER=dummy|jawis controls which CRM integration the "crm" alias resolves to
22. IntegrationFactory.get("crm") is always the right way — never call crm_dummy or crm_jawis directly
23. JawisLeadProvider wraps JawisClient — never call JawisClient directly in executors or services

## Do's
- Read every file in `/docs` before implementing
- Update documentation after every sprint
- Reuse existing APIs; no new DB tables
- Use polling (10s) not WebSockets
- Store all node config in `node.config` inside Flow JSON
- Use SchedulerService (in-process asyncio) instead of Redis/Celery

## Don'ts
- No schema changes
- No UI redesigns
- No Journey architecture changes
- No Engine architecture changes
- No Meta/WhatsApp/SMTP API calls directly in executors (use integrations)
- No hardcoded secrets (use IntegrationConfig + env vars)
- No WebSockets
- No Redis/Celery (SchedulerService uses in-process polling)

## File Location
All backend: `backend/app/`
All frontend: `frontend/src/`
Documentation: `docs/`

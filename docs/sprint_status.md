# JAWCOM — Sprint Status

## Current Sprint

| Field | Value |
|---|---|
| **Sprint** | Sprint 19 — Journey Dashboard |
| **Status** | ✅ Completed |
| **Goal** | Implement the Journey Dashboard tab (previously near-blank) — Journey Summary, Execution Metrics, Recent Executions, Flow Summary, Trigger Mapping, Integration Status, Quick Actions — using only existing services plus one new read-only integration health endpoint |

## Completed Sprints

| Sprint | Date | Description |
|---|---|---|
| Sprint 1 | — | Journey Lifecycle |
| Sprint 2 | — | Executor Framework |
| Sprint 3 | — | Node Configuration System |
| Sprint 4 | — | Flow Validation Engine |
| Sprint 5 | — | Execution Monitor & Debugger |
| Sprint 6 | — | Variables Engine |
| Sprint 7.5 | 2026-07-06 | Architecture Refinement |
| Sprint 8+9 | 2026-07-06 | Wait Scheduler & Retry Framework |
| Sprint 10+11 | 2026-07-06 | Integration Framework & Real Action Executors |
| Sprint 12+13 | 2026-07-06 | CRM Action Framework |
| Sprint 14+15 | 2026-07-06 | Human Tasks & Approval Workflow |
| Sprint 16+17 | 2026-07-06 | JAWIS Live Integration |
| Sprint 18 | 2026-07-06 | Template Management |
| Sprint 19 | 2026-07-06 | Journey Dashboard |

## Next Sprint

| Field | Value |
|---|---|
| **Sprint** | TBD |
| **Priority candidates** | Variable Filters, AI Conditions, Real WhatsApp API |
| **Decision needed** | Which sprint to prioritize next |

## Current Blockers

- None

## Known Technical Debt

1. **Old sync services in `journeys/` and `stage_mapping/` directories** — Legacy code from the initial architecture. Uses `flow_id`/`trigger_type`/`trigger_value` fields that are not read by the new execution engine. Should be cleaned up.

2. **`get_next_node_id()` in `utils.py`** — Dead code. The engine uses adjacency-based BFS traversal and does not use `result.next_node_id` for navigation (except ConditionExecutor which sets it for routing).

3. **`log_payload` in executor outputs** — Redundant. The engine already creates execution logs; `build_log_payload()` writes data that is duplicated in the output. Could be removed in a future cleanup sprint.

4. **No graceful handling of missing Flow Definition** — When `journey.flow_definition_id` is NULL, execution silently skips the journey. Should surface this as a validation error or warning.

5. **Random priority assignment in JourneyMonitor** — `PRIORITIES[Math.floor(Math.random() * PRIORITIES.length)]` is placeholder data.

6. **Frontend build warnings** — Some legacy dependencies may produce deprecation warnings.

7. **Scheduler runs in-process** — `SchedulerService` is a background asyncio task in the same process as the FastAPI app. If the app restarts, in-flight waiting instances will not be resumed until the scheduler polls again (up to 30s delay). Extraction to a separate service is recommended for production.

8. **`app/flows/services.py`/`validators.py` still reference the old sync `TemplateService(Session)` constructor** — these are part of the already-legacy, unreferenced `app/flows/` module (see debt #1) and were not updated when `TemplateService` became async in Sprint 18, since nothing imports or instantiates them. Will break if that legacy module is ever revived without also updating this call site.

9. **`app/communication/engine.py` (`CommunicationEngine`) is never instantiated anywhere** — dormant scaffold, also calls `TemplateService` synchronously. Left untouched in Sprint 18 (out of scope — not the Journey/Execution Engine).

## Known Limitations

1. **WhatsApp/Email are live by default; Notification is still simulated** — `"whatsapp"`/`"email"` call the real JAWIS Communication API (require `JAWIS_BASE_URL`/`JAWIS_API_TOKEN`; sends fail with no retry if unset). Simulated versions remain reachable via `IntegrationFactory.get("whatsapp_dummy"|"email_dummy")`, not via any env-var toggle. `NotificationIntegration` still just logs payloads.
2. **JAWIS Lead/CRM Live Integration is opt-in; Communication is not** — By default the system uses `DummyLeadProvider` and `DummyCRMIntegration` (set `JAWIS_LEAD_PROVIDER=jawis`/`JAWIS_CRM_PROVIDER=jawis` to switch). WhatsApp/Email have no such toggle — they always call JAWIS. Environment variables must be set before app startup.
3. **No WebSockets** — Real-time updates use 10-second polling.
4. **Single-tenant** — No workspace isolation for multi-tenancy. `Template.workspace_id` exists as a nullable column (FK constraint preserved at the DB level) for when this is built.
5. **Templates have no in-use enforcement beyond stage mappings and flow nodes** — `TemplateService.get_template_usage()`/delete-guard only checks `StageMapping.template_id` and `FlowDefinition.definition` JSON node configs; it does not (and cannot yet) check the dormant Campaign/Message cluster since those aren't live.
6. **Journey Dashboard's "Last Published" is approximate** — there is no dedicated `published_at` column; it shows `FlowDefinition.updated_at` when `status == "published"`. If a published flow's `definition` were edited via PATCH without re-publishing (not currently exposed in the UI), this would drift from the true last-publish time.
7. **Journey Dashboard's Average Duration only counts instances with both `started_at` and `completed_at`** — running/waiting/failed-without-completion instances are excluded from the average, matching how duration is meaningfully defined, but this means the figure can look sparse for journeys with few completed runs.

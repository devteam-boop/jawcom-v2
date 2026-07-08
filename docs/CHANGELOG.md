# JAWCOM — Changelog

## Documentation Alignment — 2026-07-07

Documentation-only pass (no code changes). Verified every architecture
document against the current implementation, closed gaps, and archived
stale docs so `docs/architecture.md` is the single canonical reference.

### Findings
- `docs/architecture.md`, `docs/AI_CONTEXT.md`, `docs/module_dependencies.md`, `docs/roadmap.md` — confirmed current and accurate, with a few real gaps closed (below).
- Root `ARCHITECTURE.md` — a 2026-07-02 redesign proposal, never implemented (frontend nav still uses the pre-proposal structure). Archived with a banner; kept for its unimplemented Inbox/Timeline/Channel-abstraction design ideas.
- Root `PROJECT_REVIEW.md` — an early-prototype snapshot (pre-domain-models), now factually wrong about current completion. Archived with a banner.
- `AI_CONTEXT/JAWCOM_MASTER_CONTEXT.md` — previously undiscovered fourth doc, self-described as "the single source of truth," describing a Sprint 1-5 snapshot (~35% complete, no product routes). Archived with a banner; its own "Update Instructions" section was neutralized to stop future dual-maintenance.
- Confirmed one still-true factual claim from that archived doc: `backend/app/providers/resend/resend_provider.py` does not exist on disk even though `app/providers/__init__.py` imports it — a real, currently-live bug in dormant code. Recorded as `KNOWN_ISSUES.md` #8.
- `docs/architecture.md`'s Module Boundaries table had no row for `app/communication/` at all, and its `events/`/`jawis/` dependency rows were wrong (said `services/`/`config/` only; actually `execution/`/`events/`).
- `docs/architecture.md` had no section on the Event Dispatcher pipeline (webhook → normalization → typed event → `EventDispatcher` → `CommunicationEventHandler` → engine), no "Communication Architecture" section distinguishing the one live send path from three dormant scaffolds, and no Running Instance state-machine/lifecycle section.
- "Data Flow: Execution Monitor" in `docs/architecture.md` was internally inconsistent with the doc's own top-of-file diagram — it omitted the Approvals/Tasks tabs and didn't name `ExecutionDrawer.jsx` as the shared component both `JourneyMonitor.jsx` and `RunningInstances.jsx` render.

### Files Changed
| File | Change |
|---|---|
| `docs/architecture.md` | Added Document Map banner; added `communication/` row + expanded `providers/` row to Module Boundaries; fixed `events/`/`jawis/` dependency rows; added "Event Dispatch Architecture", "Communication Architecture", "Running Instance Lifecycle" sections; rewrote "Data Flow: Execution Monitor" to match current `ExecutionDrawer.jsx` |
| `docs/module_dependencies.md` | Added `events/` dependency graph + table row; fixed `jawis/` row; flagged `app/communication/`, `app/providers/` as dormant |
| `docs/AI_CONTEXT.md` | Added doc-map pointer; added Event Dispatcher + dormant-scaffolds bullets to Key Components |
| `docs/KNOWN_ISSUES.md` | Added #8 — `app/providers/` broken `ResendProvider` import |
| `ARCHITECTURE.md` (root) | Added archive banner pointing to `docs/architecture.md` |
| `PROJECT_REVIEW.md` (root) | Added archive banner pointing to `docs/` |
| `AI_CONTEXT/JAWCOM_MASTER_CONTEXT.md` | Added archive banner; neutralized its own update instructions |

## JAWIS Communication Integration — 2026-07-06

### Architecture Changes
- **`JawisCommunicationIntegration`** (`app/integrations/jawis_communication.py`) — new shared base class for JAWIS Sprint-1 messaging endpoints, implementing all request/response/error handling exactly once. Two thin concrete subclasses, `JawisWhatsAppIntegration` (`POST /api/messages/whatsapp/send`) and `JawisEmailIntegration` (`POST /api/messages/email/send`), are now registered as the **default** `"whatsapp"`/`"email"` backends in `IntegrationFactory`, replacing the simulated `WhatsAppIntegration`/`EmailIntegration`.
- **Deliberate error-handling difference from `JawisCRMIntegration`**: `JawisCRMIntegration` catches failures and returns `{"success": False, ...}`, but every executor today ignores that field and always builds `ExecutionResult(success=True, ...)` — so a CRM failure never actually surfaces as a failed node. To make "JAWIS unavailable → mark execution failed" work for messaging *without touching any executor or the engine*, `JawisCommunicationIntegration` instead **raises** `JawisCommunicationError` on any failure (missing config, unreachable host, non-2xx response). The uncaught exception propagates out of `executor.execute()` into the engine's existing `_execute_node()` exception handler (`app/execution/engine.py`, unchanged), which already creates a failed log and calls `instance_service.fail()` — with no retry, since `RetryService` is a separate, manually-triggered mechanism.
- **Dummy integrations preserved for testing** — `WhatsAppIntegration`/`EmailIntegration` are still registered, now under `"whatsapp_dummy"`/`"email_dummy"` (their `.name` properties updated to match), mirroring the existing `crm_dummy`/`crm_jawis` pattern. No env-var toggle was added (unlike CRM's `JAWIS_CRM_PROVIDER`) — the task asked for a direct replacement, not a new switching mechanism, so `"whatsapp"`/`"email"` unconditionally resolve to the real JAWIS integrations now.
- **New setting `JAWIS_API_TOKEN`** — distinct from the existing `JAWIS_API_KEY` (used by `JawisClient`/`JawisLeadProvider`/`JawisCRMIntegration` for the business-data API). The messaging API uses its own bearer token.
- **No changes to `send_whatsapp_executor.py`, `send_email_executor.py`, or `engine.py`** — verified by re-running the full test suite of manual checks against a local stub JAWIS server: success responses are stored in `provider_response` byte-for-byte as received, and failures propagate uncaught through the unmodified executors.

### Files Changed
| File | Change |
|---|---|
| `backend/app/config/settings.py` | Added `JAWIS_API_TOKEN` |
| `backend/app/integrations/config.py` | Added `jawis_api_token` (masked in `to_dict()`) |
| `backend/app/integrations/jawis_communication.py` | **New** — `JawisCommunicationIntegration`, `JawisWhatsAppIntegration`, `JawisEmailIntegration`, `JawisCommunicationError` |
| `backend/app/integrations/__init__.py` | `"whatsapp"`/`"email"` now register the JAWIS classes; dummies re-registered as `"whatsapp_dummy"`/`"email_dummy"` |
| `backend/app/integrations/whatsapp.py`, `email.py` | `.name` updated to `"whatsapp_dummy"`/`"email_dummy"` to match their new registry keys (matches the `DummyCRMIntegration` convention) |

### Breaking Changes
- None for flow authors — `send_whatsapp`/`send_email` nodes are unchanged; `node.config` shape is identical.
- Operationally: with `JAWIS_BASE_URL`/`JAWIS_API_TOKEN` unset (the default in this environment today), every Send WhatsApp/Send Email node will now fail immediately instead of simulating success, since `"whatsapp"`/`"email"` no longer point at the dummy integrations. Set both env vars to restore live sending, or explicitly call `IntegrationFactory.get("whatsapp_dummy"|"email_dummy")` for local development without JAWIS configured (not currently wired to any env-var switch — see Configuration below).

## UX Refactor — Remove Duplicate Journey Information — 2026-07-06

### Architecture Changes
- **New shared `ExecutionDrawer` component** (`modules/journeys/ExecutionDrawer.jsx`) — extracted verbatim from `JourneyMonitor.jsx`'s previously-inline detail Sheet (Overview/Approvals/Tasks/Steps/Timeline/Raw tabs, Retry/Resume/Approve/Reject/Complete/Reject actions). Fully self-contained: given only an `instanceId`, it fetches the instance, its journey name, execution logs, approvals, and tasks itself (`runningInstanceService`, `journeyService`, `flowExecutionLogService`, `approvalService`, `taskService` — all pre-existing). Callers pass `instanceId`, `onClose`, and `onActionComplete` — no data fetching or drawer markup duplicated at the call sites.
- **Journey Dashboard trimmed to overview-only** — removed "Recent Executions" (the instance table) and "Trigger Mapping" (the full stage-mapping list) sections. Dashboard now shows exactly: Journey Summary, Execution Metrics (aggregated), Flow Summary, Integration Status, Quick Actions. Trigger stage is still visible as a single field inside Journey Summary; the full mapping list remains available in the Settings tab (`TriggerConfiguration`, unchanged) — no information was deleted, only de-duplicated.
- **Running Tab now opens the shared drawer** — `RunningInstances.jsx` gained its own `selectedId` state and renders `<ExecutionDrawer>` directly, wired to an `onRefresh` prop. Previously this component accepted an `onSelect` prop that `JourneyDetail.jsx` never actually passed, so clicking a row silently did nothing.
- **Journey Monitor refactored onto the same drawer** — all of its inline Sheet JSX, tab logic, action handlers (`handleRetry`/`handleResume`/`handleApprove`/`handleReject`/`handleCompleteTask`/`handleRejectTask`), `logs`/`approvals`/`tasks` state, and helpers (`formatDuration`, `MetaRow`, `NODE_STATUS_COLORS`) were deleted from `JourneyMonitor.jsx` and now live only in `ExecutionDrawer.jsx`. `INSTANCE_STATUS_TONE` is exported once from `ExecutionDrawer.jsx` and imported by `JourneyMonitor.jsx` for its table's status column, instead of being defined in both places.
- **`?instance=` deep-link simplified** — since the drawer now self-fetches from just an id, `JourneyMonitor.jsx` no longer needs to wait for its row list to load or look up a matching row; it just sets `selectedId` directly from the query param.

### Files Changed
| File | Change |
|---|---|
| `frontend/src/modules/journeys/ExecutionDrawer.jsx` | **New** — the single shared execution detail drawer |
| `frontend/src/modules/journeys/index.js` | Export `ExecutionDrawer`, `INSTANCE_STATUS_TONE` |
| `frontend/src/modules/journeys/JourneyDashboard.jsx` | Removed Recent Executions + Trigger Mapping sections and their now-unused imports/state |
| `frontend/src/modules/journeys/RunningInstances.jsx` | Owns `selectedId` state, renders `<ExecutionDrawer>`, gained `onRefresh` prop (replaces the never-wired `onSelect`) |
| `frontend/src/pages/JourneyMonitor.jsx` | Removed inline Sheet/tabs/handlers (~350 lines), renders `<ExecutionDrawer>` instead |
| `frontend/src/pages/JourneyDetail.jsx` | Extracted `fetchInstances` callback, passed as `onRefresh` to `<RunningInstances>` |

### Components Reused (no duplication introduced)
`Sheet`/`SheetContent`/`SheetHeader`/`SheetTitle`, `Tabs`/`TabsList`/`TabsTrigger`/`TabsContent`, `StatusBadge`, `Avatar`/`AvatarFallback`, `Separator`, `Badge`, `Button` — all pre-existing shadcn/ui + shared components, reused as-is inside the one new `ExecutionDrawer`. Services reused unchanged: `runningInstanceService`, `journeyService`, `flowExecutionLogService`, `approvalService`, `taskService`. No new backend endpoints, no new database access patterns.

### Breaking Changes
- None. `RunningInstances`'s `onSelect` prop is removed since it was never wired to anything — no functioning call site depended on it.

### QA Steps
1. Running Tab (inside a journey): click a row → same drawer, same tabs, same Retry/Resume/Approve/Reject actions as before → closing/acting refreshes that journey's instance list only.
2. Journey Monitor: click a row → identical drawer content and behavior to before the refactor.
3. Journey Dashboard: confirm Recent Executions and Trigger Mapping are gone; Journey Summary still shows the trigger stage; Settings tab still shows the full trigger mapping list.
4. `/journeys?instance=<id>` deep link still opens the correct instance's drawer on Journey Monitor.
5. `npm run build` — clean, bundle size decreased vs. pre-refactor (confirms removed duplication, not added).

## Sprint 19 — Journey Dashboard — 2026-07-06

### Architecture Changes
- **`JourneyDashboard.jsx` implemented** — previously a minimal stub (5 stat cards + a placeholder card), now covers all 7 required sections: Journey Summary, Execution Metrics, Recent Executions, Flow Summary, Trigger Mapping, Integration Status, Quick Actions. No new database tables; every metric is computed client-side from data already returned by existing endpoints.
- **New read-only endpoint `GET /api/integrations/health`** (`app/api/integration_routes.py`) — the only backend addition. Calls the already-implemented `IntegrationFactory.get("whatsapp"|"email"|"crm").health()` (existing `BaseIntegration.health()` contract, unchanged) and derives a JAWIS status from the existing `IntegrationConfig`. This was the one genuinely missing piece — `docs/api_contract.md` already noted "a future health dashboard UI can call this method"; this sprint is that UI. Zero new business logic, purely exposes existing, already-correct logic over HTTP for the first time.
- **Frontend `integrationService` gained one method** (`getHealth()`) — added to the existing (previously orphaned/unused) `frontend/src/services/integrations.js` rather than creating a second integrations service file.
- **Deep-linking from Dashboard → Journey Monitor** — Recent Executions rows navigate to `/journeys?instance=<id>`; `JourneyMonitor.jsx` gained a small effect that reads the `instance` query param and calls its own existing `handleSelect()` to open the same detail Sheet used for a normal row click, then clears the param. No new selection logic — reuses the existing handler.
- **Quick Actions reuse `JourneyDetail.jsx`'s existing `handleAction`/`setTestOpen`/tab-switch handlers** via props — no duplicate activate/pause/archive network calls.

### Files Changed
| File | Change |
|---|---|
| `backend/app/api/integration_routes.py` | **New** — `GET /api/integrations/health` |
| `backend/app/api/__init__.py`, `backend/app/main.py` | Register `integration_router` |
| `frontend/src/services/integrations.js` | Added `getHealth()` |
| `frontend/src/modules/journeys/JourneyDashboard.jsx` | Rewritten — all 7 sections, empty states, no mock data |
| `frontend/src/pages/JourneyDetail.jsx` | Pass `mappings`, `actionLoading`, `onAction`, `onTestJourney`, `onOpenFlow` into `<JourneyDashboard>` |
| `frontend/src/pages/JourneyMonitor.jsx` | Added `?instance=` deep-link auto-select effect |

### Breaking Changes
- None.

### QA Steps
1. Open a journey with running instances, a published flow, and a trigger mapping — confirm all 7 sections render real data (verified live against journey "Final_testing_1": 2 running instances, 6 nodes/6 edges, valid flow, 1 trigger mapping, integration health all reflecting actual `.env` configuration).
2. Open a brand-new/empty journey — confirm Execution Metrics, Recent Executions, Flow Summary, and Trigger Mapping each show their `EmptyState` instead of blank space or errors.
3. Click a Recent Executions row → confirm it navigates to Journey Monitor and opens that instance's detail Sheet.
4. Click Pause/Resume/Archive/Test Journey/Open Flow from Quick Actions — confirm each reuses the same behavior as the equivalent button in the page header / Flow tab.

## Sprint 18 — Template Management — 2026-07-06

### Architecture Changes
- **Single template model** — `Template` (`templates` table) is now the sole template model. `CustomTemplate`/`custom_templates` (never migrated, never reachable via any route) is removed entirely.
- **`Template` decoupled from the dormant Workspace/Campaign/Message cluster** — that cluster's module is never imported anywhere in the app and `Journey` has no matching side of `Workspace.journeys`, so declaring `Template.workspace = relationship("Workspace", ...)` or `ForeignKey('workspaces.id')` in the ORM crashes at first flush (`NoReferencedTableError`)/mapper-configure time. `templates.workspace_id` is now a plain nullable UUID column (no ORM relationship, no Python-level FK) — the physical DB FK constraint from the initial migration is left in place for when workspace scoping is actually built.
- **`app/templates/services.py` rewritten to async** — `TemplateService` now takes an `AsyncSession` and uses `TemplateRepository` (new, follows the existing repository pattern), instead of a synchronous `Session` querying `CustomTemplate` directly. `TemplateValidator` and `TemplateRenderer` are reused unchanged.
- **`/api/templates` CRUD + duplicate/archive/usage** — new `template_routes.py`, registered in `main.py`.
- **Template resolution in execution** — `ExecutionContext` gained a `template_service` field (mirrors the existing `resolver`/`renderer` fields), populated by the engine at both `ExecutionContext` construction sites (`_execute_for_stage`, `_resume_from`). `SendWhatsAppExecutor`/`SendEmailExecutor` resolve `node.config.template_id` via `exec_ctx.template_service.get_template(...)` before building the integration payload — the DB lookup lives in the service, not the executor (same layering as `LeadProvider` → `ExecutionContext` → executor). Legacy `node.config.template_name` (free text) is still honored when `template_id` is absent.
- **Flow Builder template selector** — `PropertiesPanel.jsx`'s `send_whatsapp`/`send_email` config now shows a `Select` populated from `GET /api/templates?channel=...`, storing `template_id` in `node.config` instead of a free-text template name. The existing variable `PreviewButton` now previews the selected template's real content/subject.
- **Frontend Templates page wired to the real API** — `pages/Templates.jsx` now uses `templateService`/`useTemplates` (fixed: it previously imported from the wrong barrel file and was never wired to any page) instead of `dummy-data/templates.js`. Implements List, Create, Edit, Delete, Duplicate, Archive, Preview.
- **Removed duplicate/orphaned frontend components** — `modules/templates/TemplateList.jsx` and `TemplatePreview.jsx` were unused, buggy (missing import), parallel reimplementations of the same list+preview UI already inline in `pages/Templates.jsx`; deleted per "avoid duplicate template systems."
- **New dependency**: `jinja2` (was imported by `app/templates/renderer.py` but never installed or added to `requirements.txt` — the renderer had never actually been run before this sprint).

### Files Changed
| File | Change |
|---|---|
| `backend/app/models/template.py` | Removed broken `Workspace` relationship/FK; `workspace_id` now plain nullable UUID |
| `backend/app/models/custom_template.py` | **Deleted** |
| `backend/app/models/__init__.py` | Export `Template`/`TemplateChannel`/`TemplateStatus` instead of `CustomTemplate` |
| `backend/alembic/versions/f1a2b3c4d5e6_make_templates_workspace_id_nullable.py` | **New migration** — `templates.workspace_id` nullable (applied) |
| `backend/app/repositories/template_repository.py` | **New** — async repository for `Template` |
| `backend/app/repositories/stage_mapping_repository.py` | Added `get_by_template_id()` (used by usage-check) |
| `backend/app/templates/schemas.py` | Rewritten for `Template`'s fields (`status` added, `module` removed, `TemplateVersionSchema` removed — unused) |
| `backend/app/templates/services.py` | Rewritten async, queries `Template`; added `duplicate_template`, `archive_template`, real `get_template_usage` |
| `backend/app/templates/__init__.py` | Drop `TemplateVersionSchema` export |
| `backend/app/api/template_routes.py` | **New** — full CRUD + duplicate/archive/usage routes |
| `backend/app/api/__init__.py`, `backend/app/main.py` | Register `template_router` |
| `backend/app/execution/executors/base.py` | `ExecutionContext` gained `template_service` field |
| `backend/app/execution/engine.py` | Construct `TemplateService(session)` and attach to `exec_ctx` at both construction sites |
| `backend/app/execution/executors/send_whatsapp_executor.py` | Resolve `template_id` → template name via `exec_ctx.template_service`, fallback to legacy `template_name` |
| `backend/app/execution/executors/send_email_executor.py` | Resolve `template_id` → subject/content via `exec_ctx.template_service`, fallback to legacy `template_name`/`subject` |
| `backend/requirements.txt` | Added `jinja2==3.1.6` |
| `frontend/src/services/templates.js` | Added `delete`/`duplicate`/`archive`; fixed `list` filter handling |
| `frontend/src/modules/templates/hooks/useTemplates.js` | Fixed broken import (`@/services` → `@/services/templates`) |
| `frontend/src/modules/templates/index.js` | Drop `TemplateList`/`TemplatePreview` exports |
| `frontend/src/modules/templates/TemplateList.jsx`, `TemplatePreview.jsx` | **Deleted** (unused, buggy duplicates) |
| `frontend/src/pages/Templates.jsx` | Rewritten to use the real API instead of dummy data; List/Create/Edit/Delete/Duplicate/Archive/Preview implemented |
| `frontend/src/modules/journeys/FlowBuilder/PropertiesPanel.jsx` | `send_whatsapp`/`send_email` template name input replaced with a `Select` (`TemplateSelectField`) storing `template_id` |

### Breaking Changes
- None for running flows — `template_name` free text is still read by both executors when `template_id` is absent, so existing published flows keep executing unchanged. New/edited flows store `template_id` instead.
- `frontend/src/pages/Campaigns.jsx` still uses `dummy-data/templates.js` independently (out of scope for this sprint — a separate, dormant Campaigns feature) and is unaffected by this change.

### QA Steps
1. Backend: `alembic upgrade head`, then `POST /api/templates` → `GET /api/templates` → `PATCH` → `POST .../duplicate` → `POST .../archive` → `GET .../usage` → `DELETE`.
2. Frontend: open Template Library, create a WhatsApp and an Email template, verify list/preview/variables tab, duplicate, archive, delete (and confirm delete is blocked once referenced by a flow node).
3. Flow Builder: add a Send WhatsApp/Send Email node, confirm the Template dropdown lists templates for that channel, select one, verify the Preview button shows resolved sample values.
4. Execution: run **Test Execution** against a journey whose flow uses a `template_id`-based node; confirm the execution log's `resolved_template_name`/`resolved_content` reflect the real template row, not a literal string.
5. Backward compatibility: run a previously-published flow that still has `template_name` (no `template_id`) and confirm it still executes successfully.

## UI Bug Fix — Layout & Scrolling — 2026-07-06

### Architecture Changes
- None (layout/CSS-only fix; no business logic, schema, or UI redesign changes)

### Root Cause
- `AppLayout`'s `<main>` (the single element wrapping every routed page via `<Outlet/>`) had `flex-1` but no `min-h-0`/`overflow-y-auto`. Per CSS flex rules, a flex item's automatic minimum height is content-based unless overflow is set to non-`visible` — so `<main>` grew to fit page content instead of clipping to the viewport, and the outer `overflow-hidden` shell then clipped that overflow instead of scrolling it. This affected every page in the app.
- Two nested spots in `JourneyDetail.jsx` (`Flow` tab content wrappers) had the same missing `min-h-0` on a `flex-1` ancestor of a `h-full`-sized `FlowBuilder`.
- The shared `DialogContent` primitive had no `max-h`/`overflow-y-auto`, so any dialog whose form content exceeded the viewport (e.g. Stage Mapping edit dialog) could clip fields/buttons with no way to scroll to them.

### Files Changed
| File | Change |
|---|---|
| `frontend/src/layouts/AppLayout.jsx` | Added `min-h-0` to the header/main column and `min-h-0 overflow-y-auto` to `<main>`, making it the single predictable scroll container for every page |
| `frontend/src/pages/JourneyDetail.jsx` | Added `min-h-0` to the two `flex-1` wrappers around `FlowBuilder` (wizard "flow" step and tabbed "flow" section) |
| `frontend/src/components/ui/dialog.jsx` | Added `max-h-[90vh] overflow-y-auto` to the base `DialogContent` so any dialog scrolls internally instead of clipping at 100vh+ |

### Breaking Changes
- None — purely additive Tailwind utility classes; no component APIs, business logic, or visual design changed

---

## Sprint 16+17 — 2026-07-06

### Architecture Changes
- **JAWIS Lead Provider** — NEW `JawisLeadProvider` implementing the `LeadProvider` interface, wrapping the existing `JawisClient` to fetch real lead/company/owner/stage data from the JAWIS Business OS API
- **JAWIS CRM Integration** — NEW `JawisCRMIntegration` replacing the simulated `DummyCRMIntegration`; makes real API calls to JAWIS for all 6 CRM actions (update_lead, update_company, assign_owner, change_stage, create_task, create_note)
- **Configuration-driven switching** — Both providers are switchable by environment variable:
  - `JAWIS_LEAD_PROVIDER=dummy|jawis` (default: `dummy`)
  - `JAWIS_CRM_PROVIDER=dummy|jawis` (default: `dummy`)
- **Integration alias pattern** — `IntegrationFactory` now supports `register_alias()`, allowing `"crm"` to resolve to either `"crm_dummy"` or `"crm_jawis"` based on the env var; executors continue to call `IntegrationFactory.get("crm")` unchanged
- **LeadProviderFactory** — `get_provider()` now defaults to `JAWIS_LEAD_PROVIDER` env var instead of hardcoded `"dummy"`; the engine calls `get_provider()` with no arguments and gets the configured backend
- **Settings** — Added `JAWIS_BASE_URL`, `JAWIS_API_KEY`, `JAWIS_WORKSPACE`, `JAWIS_LEAD_PROVIDER`, `JAWIS_CRM_PROVIDER`
- **Zero engine/executor changes** — No modifications to ExecutionEngine, ExecutorFactory, or any executor. All switching is handled at the factory layer.

### Files Changed
| File | Change |
|---|---|
| `backend/app/config/settings.py` | Added `JAWIS_BASE_URL`, `JAWIS_API_KEY`, `JAWIS_WORKSPACE`, `JAWIS_LEAD_PROVIDER`, `JAWIS_CRM_PROVIDER` |
| `backend/app/execution/providers/jawis_lead_provider.py` | **New file** — `JawisLeadProvider` wraps `JawisClient.get_lead_context()`, returns same dict shape as `DummyLeadProvider` |
| `backend/app/execution/providers/lead_provider.py` | `get_provider()` now reads `JAWIS_LEAD_PROVIDER` env var as default name; registered `JawisLeadProvider` |
| `backend/app/execution/providers/__init__.py` | Export `JawisLeadProvider` |
| `backend/app/integrations/crm.py` | Renamed `CRMIntegration` to `DummyCRMIntegration` (name=`crm_dummy`) |
| `backend/app/integrations/jawis_crm.py` | **New file** — `JawisCRMIntegration` routes each CRM action to the corresponding JAWIS API endpoint |
| `backend/app/integrations/factory.py` | Added `register_alias()` + env-var-based alias for `"crm"` → `"crm_dummy"` or `"crm_jawis"` |
| `backend/app/integrations/config.py` | Added JAWIS fields to `IntegrationConfig` + `to_dict()` |
| `backend/app/integrations/__init__.py` | Register both `crm_dummy` and `crm_jawis` backends |

### Breaking Changes
- None — all existing APIs maintained; `DummyCRMIntegration` is the default when `JAWIS_CRM_PROVIDER` is unset; `JawisLeadProvider` is opt-in via `JAWIS_LEAD_PROVIDER=jawis`

---

## Sprint 14+15 — 2026-07-06

### Architecture Changes
- **Human Tasks & Approval Workflow** — NEW two node types (`approval`, `manual_task`) that pause journey execution for human interaction
- **New statuses** — `waiting_approval` and `waiting_task` added to `InstanceStatus` enum (no schema change — stored in existing `data` JSON column)
- **ApprovalExecutor** — pauses instance (status=waiting_approval), creates approval record in `instance.data.approvals`, sets `_halt=approval`
- **ManualTaskExecutor** — pauses instance (status=waiting_task), creates task record in `instance.data.tasks`, sets `_halt=task`
- **ApprovalService** — list/get/approve/reject approvals stored in instance.data JSON
- **TaskService** — list/get/complete/reject tasks stored in instance.data JSON
- **Engine updated** — existing `status="skipped"` handler extended to handle `_halt` flag (approval/task); no architecture redesign
- **Resume reuses existing framework** — when approval is approved or task is completed, `engine.resume_instance(id)` is called (same path as Wait/Delay resume)
- **Frontend** — both node types have palette entries, renderers, config forms; Execution Monitor shows new status badges; detail drawer has Approvals/Tasks tabs with action buttons (Approve/Reject/Complete)

### Files Changed
| File | Change |
|---|---|
| `backend/app/models/running_journey_instance.py` | Added `WAITING_APPROVAL`, `WAITING_TASK` to `InstanceStatus` enum |
| `backend/app/runtime/schemas.py` | Added `waiting_approval`, `waiting_task` to `InstanceStatus` schema |
| `backend/app/execution/executors/approval_executor.py` | **New file** — creates approval, returns skipped with _halt=approval |
| `backend/app/execution/executors/manual_task_executor.py` | **New file** — creates task, returns skipped with _halt=task |
| `backend/app/execution/executors/__init__.py` | Export ApprovalExecutor, ManualTaskExecutor |
| `backend/app/execution/executors/factory.py` | Register approval, manual_task (16 executors total) |
| `backend/app/execution/engine.py` | Extended skipped handler for _halt (approval/task) — stores data in instance JSON, calls wait_approval/wait_task |
| `backend/app/services/approval_service.py` | **New file** — CRUD for approvals via instance.data JSON |
| `backend/app/services/task_service.py` | **New file** — CRUD for tasks via instance.data JSON |
| `backend/app/services/running_instance_service.py` | Added `wait_approval()`, `wait_task()` methods |
| `backend/app/api/approval_routes.py` | **New file** — GET list, POST approve/reject |
| `backend/app/api/task_routes.py` | **New file** — GET list, POST complete/reject |
| `backend/app/api/__init__.py` | Export approval_router, task_router |
| `backend/app/main.py` | Include approval_router, task_router |
| `backend/app/services/flow_validation_service.py` | Added validation for approval (approver+title) and manual_task (assignee+title) |
| `frontend/src/constants/flowNodes.js` | Added approval (ThumbsUp, cyan) and manual_task (ClipboardList, orange) |
| `frontend/src/modules/journeys/FlowBuilder/nodes/ApprovalNode.jsx` | **New file** |
| `frontend/src/modules/journeys/FlowBuilder/nodes/ManualTaskNode.jsx` | **New file** |
| `frontend/src/modules/journeys/FlowBuilder/nodes/index.js` | Export both new nodes |
| `frontend/src/modules/journeys/FlowBuilder/FlowBuilder.jsx` | NODE_TYPES map includes approval, manual_task |
| `frontend/src/modules/journeys/FlowBuilder/PropertiesPanel.jsx` | Config forms for approval (approver, title, description, timeout, type) and manual_task (assignee, title, description, due_date, priority) |
| `frontend/src/pages/JourneyMonitor.jsx` | Added status tones/filters for waiting_approval/waiting_task; Approvals/Tasks tabs in detail drawer with action buttons; Resume button supports all waiting statuses |
| `frontend/src/services/approvals.js` | **New file** — API client for approval endpoints |
| `frontend/src/services/tasks.js` | **New file** — API client for task endpoints |

### Breaking Changes
- None (all existing APIs maintained; new endpoints only)

---

## Sprint 12+13 — 2026-07-06

### Architecture Changes
- **CRM Action Framework** — NEW 6 node types (update_lead, update_company, assign_owner, change_lead_stage, create_crm_task, create_note) for CRM record management
- **CRMIntegration** — NEW integration under Integration Framework (simulated, logs payload)
- **14 executors** — executor registry grows from 8 to 14

---

## Sprint 10+11 — 2026-07-06

### Architecture Changes
- **Integration Layer** — NEW `app/integrations/` package with `BaseIntegration` ABC, `IntegrationFactory` registry, and three concrete integrations (WhatsApp, Email, Notification)
- **Executors refactored** — `SendWhatsAppExecutor`, `SendEmailExecutor`, `NotificationExecutor` now build request payloads and delegate to `IntegrationFactory.get(...).execute(payload)` instead of building payloads internally
- **IntegrationConfig** — loads all secrets (API keys, tokens) from environment settings; no hardcoded credentials
- **Health framework** — every integration implements `health()` returning status (`healthy`, `unconfigured`, `error`)
- **Settings** — added `WHATSAPP_API_KEY`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_ACCESS_TOKEN`, `EMAIL_PROVIDER`, `EMAIL_API_KEY`, `EMAIL_SENDER`

### Files Changed
| File | Change |
|---|---|
| `backend/app/integrations/__init__.py` | **New file** — package exports + auto-registration |
| `backend/app/integrations/base.py` | **New file** — BaseIntegration ABC |
| `backend/app/integrations/factory.py` | **New file** — IntegrationFactory registry |
| `backend/app/integrations/config.py` | **New file** — IntegrationConfig from settings |
| `backend/app/integrations/whatsapp.py` | **New file** — WhatsAppIntegration (simulated) |
| `backend/app/integrations/email.py` | **New file** — EmailIntegration (simulated) |
| `backend/app/integrations/notification.py` | **New file** — NotificationIntegration (simulated) |
| `backend/app/config/settings.py` | Added 7 integration settings fields |
| `backend/app/execution/executors/send_whatsapp_executor.py` | Delegate to WhatsAppIntegration |
| `backend/app/execution/executors/send_email_executor.py` | Delegate to EmailIntegration |
| `backend/app/execution/executors/notification_executor.py` | Delegate to NotificationIntegration |

### Breaking Changes
- None (executor output includes new `provider_response` key, backward-compatible)

---

## Sprint 8+9 — 2026-07-06

### Architecture Changes
- **WaitExecutor** now calculates `resume_at` and returns `status="skipped"` with `_wait: True` — pauses instance to `waiting`
- **DelayExecutor** returns `status="skipped"` with `resume_at` (no status change, instance stays `running`)
- **Engine** handles `status="skipped"` result — transitions instance to waiting or stores resume_at, stops traversal
- **Engine** gained `resume_instance()`, `retry_node()`, `retry_journey()` public methods
- **SchedulerService** — NEW background asyncio task that polls for waiting instances with expired `resume_at` and resumes them
- **RetryService** — NEW retry logic with policy (default 3 retries, delays [60s, 300s, 1800s]), supports node-level and journey-level retry
- **RunningInstanceService** — added `wait()` and `find_waiting()` methods
- **No database schema changes** — `retry_count`, `resume_at`, `retry_policy` all stored in `instance.data` JSON
- **Frontend** — Retry button enabled for failed instances, Resume button enabled for waiting instances, `resume_at` and `retry_count` shown in detail drawer

### Files Changed
| File | Change |
|---|---|
| `backend/app/execution/executors/wait_executor.py` | Calculate resume_at, return status="skipped" with `_wait` flag |
| `backend/app/execution/executors/delay_executor.py` | Calculate resume_at, return status="skipped" (no `_wait`) |
| `backend/app/execution/engine.py` | Handle skipped status, add resume_instance / retry_node / retry_journey / _resume_from methods |
| `backend/app/services/running_instance_service.py` | Added `wait()`, `find_waiting()` methods |
| `backend/app/services/wait_scheduler_service.py` | **New file** — background poller for waiting instances |
| `backend/app/services/retry_service.py` | **New file** — retry with policy enforcement |
| `backend/app/api/running_instance_routes.py` | Added `POST /{id}/retry`, `POST /{id}/resume` endpoints |
| `backend/app/config/settings.py` | Added `SCHEDULER_ENABLED`, `SCHEDULER_POLL_INTERVAL` |
| `backend/app/main.py` | Start scheduler background task on startup, stop on shutdown |
| `frontend/src/services/runningInstances.js` | Added `retry()`, `resume()` API calls |
| `frontend/src/pages/JourneyMonitor.jsx` | Enable Retry button (failed only), Resume button (waiting only), show resume_at/retry_count in overview |

### Breaking Changes
- None (all existing APIs maintained; retry/resume are new POST endpoints)

---

## Sprint 7.5 — 2026-07-06

### Architecture Changes
- Created `LeadProviderFactory` with registry pattern (replaces direct `DummyLeadProvider()` instantiation)
- Created `TemplateRendererService` (separates `{{...}}` rendering from variable path resolution)
- Updated `ExecutionContext` to expose both `resolver` and `renderer`

### Files Changed
| File | Change |
|---|---|
| `backend/app/execution/providers/lead_provider.py` | Added `LeadProviderFactory` |
| `backend/app/execution/providers/__init__.py` | Export `LeadProviderFactory` |
| `backend/app/services/template_renderer_service.py` | **New file** |
| `backend/app/services/variable_resolver_service.py` | Added public `resolve_path()` method |
| `backend/app/execution/executors/base.py` | Added `renderer` field to `ExecutionContext` |
| `backend/app/execution/engine.py` | Use `LeadProviderFactory.get_provider()`, wire renderer |
| `backend/app/execution/executors/send_whatsapp_executor.py` | Use `renderer.render()` |
| `backend/app/execution/executors/send_email_executor.py` | Use `renderer.render()` |
| `backend/app/execution/executors/notification_executor.py` | Use `renderer.render()` |
| `backend/app/execution/executors/condition_executor.py` | Use `renderer.render()` / `renderer.resolve_path()` |

### Breaking Changes
- None (all existing APIs maintained)

---

## Sprint 6 — 2026-07-06

### Features
- `VariableResolverService` — resolves `{{variable.path}}` from runtime context
- Real Condition comparison engine (7 operators: equals, not_equals, greater_than, less_than, contains, starts_with, ends_with)
- `DummyLeadProvider` for lead/company data
- `ExecutionContext` dataclass with lead, company, resolver
- Variable resolution in SendWhatsApp, SendEmail, Notification executors
- Frontend variable preview (PreviewButton in PropertiesPanel)
- Added `starts_with`/`ends_with` operators to condition dropdown

### Files Changed
| File | Change |
|---|---|
| `backend/app/services/variable_resolver_service.py` | **New file** |
| `backend/app/execution/providers/lead_provider.py` | **New file** |
| `backend/app/execution/providers/__init__.py` | **New file** |
| `backend/app/execution/executors/base.py` | Updated `ExecutionContext` |
| `backend/app/execution/executors/condition_executor.py` | Real comparison engine |
| `backend/app/execution/executors/send_whatsapp_executor.py` | Variable resolution |
| `backend/app/execution/executors/send_email_executor.py` | Variable resolution |
| `backend/app/execution/executors/notification_executor.py` | Variable resolution |
| `backend/app/execution/engine.py` | Build/use ExecutionContext |
| `frontend/src/modules/journeys/FlowBuilder/PropertiesPanel.jsx` | PreviewButton, new operators |

---

## Sprint 5 — 2026-07-06

### Features
- Running Instance detail drawer (Sheet) with 4 tabs: Overview, Steps, Timeline, Raw JSON
- Execution timeline from `FlowExecutionLog` entries
- Node status indicators (green/blue/red/gray dots)
- Execution summary (started/completed/duration/current node)
- Error display (failed node + reason + timestamp)
- Auto-refresh (10s polling) + manual refresh button
- Search by lead_id and current_node_id
- Disabled Retry button placeholder
- Enhanced `RunningInstances.jsx` with onRowClick and more columns
- Auto-refresh in `useRunningInstances` hook

### Files Changed
| File | Change |
|---|---|
| `frontend/src/pages/JourneyMonitor.jsx` | Major enhancement |
| `frontend/src/modules/journeys/RunningInstances.jsx` | Enhanced columns |
| `frontend/src/modules/journeys/hooks/useRunningInstances.js` | Auto-refresh added |

---

## Sprint 4 — 2026-07-06

### Features
- `FlowValidationService` — static graph validation + node configuration validation
- Validation rules: exactly 1 trigger, at least 1 end, no orphan nodes, all nodes reachable, no cycles, duration>0
- `POST /{id}/validate` endpoint
- Publish endpoint auto-runs validation (returns 400 on failure)
- Frontend validate button with spinner
- Validation result banner (errors/warnings)
- Publish button disabled on validation errors

### Files Changed
| File | Change |
|---|---|
| `backend/app/services/flow_validation_service.py` | **New file** |
| `backend/app/flow_definitions/schemas.py` | Validation schemas |
| `backend/app/api/flow_definition_routes.py` | Validate endpoint, updated publish |
| `backend/app/services/flow_definition_service.py` | Validation on publish |
| `frontend/src/modules/journeys/FlowBuilder/FlowToolbar.jsx` | Validate button |
| `frontend/src/modules/journeys/FlowBuilder/FlowBuilder.jsx` | Validation banner |
| `frontend/src/modules/journeys/hooks/useFlowBuilder.js` | Validate/publish state |
| `frontend/src/services/flowDefinitions.js` | Validate API call |

---

## Sprint 3 — 2026-07-06

### Features
- Node Configuration System — every node type exposes configurable properties
- Configuration stored in `node.config` inside Flow Definition JSON
- `PropertiesPanel.jsx` with per-type config forms
- All 8 executors read from `node.get("config")`
- ReactFlow data mapping: `toApiNodes()` / `toRfNodes()` handle config serialization

### Files Changed
| File | Change |
|---|---|
| `frontend/src/modules/journeys/FlowBuilder/PropertiesPanel.jsx` | Per-type config forms |
| `frontend/src/modules/journeys/FlowBuilder/FlowBuilder.jsx` | Config data mapping |
| All 8 executor files | Read from `node.get("config")` |

---

## Sprint 2 — 2026-07-06

### Features
- `BaseNodeExecutor` ABC with `ExecutionResult` dataclass
- `ExecutorFactory` registry with all 8 executors
- Engine refactored to dispatch via factory
- `build_log_payload()` / `get_next_node_id()` in utils.py
- All executors are Sprint 2 stubs (log + return success)

### Files Changed
| File | Change |
|---|---|
| `backend/app/execution/executors/base.py` | **New file** |
| `backend/app/execution/executors/factory.py` | **New file** |
| `backend/app/execution/executors/trigger_executor.py` | **New file** |
| `backend/app/execution/executors/condition_executor.py` | **New file** |
| `backend/app/execution/executors/delay_executor.py` | **New file** |
| `backend/app/execution/executors/wait_executor.py` | **New file** |
| `backend/app/execution/executors/send_whatsapp_executor.py` | **New file** |
| `backend/app/execution/executors/send_email_executor.py` | **New file** |
| `backend/app/execution/executors/notification_executor.py` | **New file** |
| `backend/app/execution/executors/end_executor.py` | **New file** |
| `backend/app/execution/executors/utils.py` | **New file** |
| `backend/app/execution/engine.py` | Refactored to use factory |

---

## Sprint 1 — 2026-07-06

### Features
- Journey lifecycle: Lead Stage Changed → Stage Mapping → Journey → Flow Definition → Running Instance → Execution Engine → Execution Logs
- `ExecutionEngine` class with BFS traversal
- `RunningJourneyInstance` model with status lifecycle (running → completed/failed)
- `FlowExecutionLog` model with status tracking
- Test execution endpoint `POST /api/execution/test`
- Event system (`LeadCreatedEvent`, `LeadStageChangedEvent`)
- `JawisClient` for external JAWIS API integration

### Files Changed
- Initial project scaffold with all models, services, routes, and execution engine

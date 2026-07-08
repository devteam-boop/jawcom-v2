# JAWCOM — Known Issues & Technical Debt

## Current Technical Debt

### 1. Legacy Sync Services
**Location:** `backend/app/journeys/services.py`, `backend/app/stage_mapping/services.py`, `backend/app/flows/services.py`

These directories contain old sync implementations from the initial architecture. They use `flow_id`/`trigger_type`/`trigger_value` fields that are not read by the new execution engine. Should be cleaned up in a future sprint.

**Impact:** Low — they are not imported or used by the new code.

**Update (Sprint 18):** `app/flows/services.py`/`validators.py` still construct `TemplateService` with the pre-Sprint-18 synchronous `Session` signature — `TemplateService` is now async (`AsyncSession`). This was not updated because nothing imports or instantiates `FlowManagerService`/`FlowValidator` anywhere in the live app. Will need a fix if this legacy module is ever revived.

### 2. Dead Code in utils.py
**File:** `backend/app/execution/executors/utils.py`

- `get_next_node_id()` — The engine uses adjacency-based BFS traversal and does not use `result.next_node_id` for navigation (except ConditionExecutor which uses config-based routing).
- `build_log_payload()` — Creates a log payload dict that executors embed in their output. The engine already creates execution logs independently. This duplicates logging metadata.

**Impact:** Low — the functions still work but produce redundant data.

### 3. No Graceful Handling of Missing Flow Definition
**File:** `backend/app/execution/engine.py` (line ~157-162)

When `journey.flow_definition_id` is NULL, the engine logs an error and silently continues to the next mapping. Should surface this as a validation error or warning to the user.

**Impact:** Medium — silent failure during execution.

### 4. Random Priority Assignment
**File:** `frontend/src/pages/JourneyMonitor.jsx`

```javascript
priority: PRIORITIES[Math.floor(Math.random() * PRIORITIES.length)]
```

Priorities in the monitor table are randomly assigned placeholder values.

**Impact:** Low — cosmetic only.

### 5. No Formal Test Coverage
No pytest or React Testing Library tests exist. All QA is manual.

**Impact:** High — risky for future changes.

### 6. Engine Session Handling
**File:** `backend/app/execution/engine.py`

The engine creates its own database session internally rather than receiving one. This makes it harder to test and transactionally integrate with callers.

**Impact:** Medium — limits testability.

### 7. `CommunicationEngine` Is Dormant Scaffold
**File:** `backend/app/communication/engine.py`

`CommunicationEngine` takes a `TemplateService` and calls it synchronously (`self.template_service.get_template(...)` without `await`), which no longer matches `TemplateService`'s async signature (Sprint 18). This was not fixed because `CommunicationEngine` is never instantiated anywhere in the codebase — a pure orphan.

**Impact:** Low — unreachable dead code, but will break immediately if anyone tries to actually use it.

### 8. `app/providers/` Is a Second, Disconnected Provider Abstraction — and Its Import Is Broken
**Files:** `backend/app/providers/__init__.py`, `backend/app/providers/registry/provider_registry.py`

There are two unrelated "provider" concepts in the codebase:
- The **live** one: `app/execution/providers/` (`LeadProviderFactory`) and `app/integrations/` (`IntegrationFactory`) — what the engine and executors actually use.
- A **second, dormant** one: `app/providers/` (`ProviderRegistry`, `Channel` enum, `MetaProvider`, and a referenced-but-nonexistent `ResendProvider`). Nothing in the live app imports `app.providers` — confirmed via repo-wide search, only its own `__init__.py` references it.

`app/providers/__init__.py` does `from .resend.resend_provider import ResendProvider`, but **`backend/app/providers/resend/` does not exist on disk at all.** If anything ever imports `app.providers` (or `app.providers.meta`, since Python still executes the package `__init__.py`), it will raise `ModuleNotFoundError` immediately.

**Impact:** Low today (nothing imports it, so the break is silent), but this module is the natural extension point for real Meta Cloud API / Resend integrations (see `docs/roadmap.md` Sprint 22, "Real Meta WhatsApp API"). Anyone picking it up will hit an immediate import error before writing a single line of new code. Either delete `app/providers/` (its intended role is fully covered by `app/integrations/`) or create the missing `resend/resend_provider.py` stub — do not build on top of it as-is.

## Known Limitations

### Functional
| Limitation | Details | Future Sprint |
|---|---|---|
| WhatsApp integration is live by default | `"whatsapp"` now calls the real JAWIS Communication API (`POST /api/messages/whatsapp/send`); requires `JAWIS_BASE_URL`/`JAWIS_API_TOKEN` set or every send fails with no retry. Simulated version still available via `IntegrationFactory.get("whatsapp_dummy")` | Done |
| Email integration is live by default | Same as above, `"email"` → `POST /api/messages/email/send`; simulated fallback is `"email_dummy"` | Done |
| No env-var toggle for whatsapp/email dummy↔jawis | Unlike CRM's `JAWIS_CRM_PROVIDER` alias, `"whatsapp"`/`"email"` unconditionally resolve to the JAWIS integrations — switching to `_dummy` requires calling `IntegrationFactory.get("whatsapp_dummy")` explicitly in code, not an env var | Future (if needed) |
| CRM integration simulated by default | Logs payload, no real CRM API (`JAWIS_CRM_PROVIDER=jawis` switches to live) | Future |
| DummyLeadProvider | Returns hardcoded data | Future |
| No variable filters | `{{upper(lead.name)}}` not supported | Sprint 16 |
| No AI conditions | Condition evaluation uses simple comparison only | Sprint 17 |
| Approvals/Tasks stored in JSON column | No dedicated tables, querying across instances requires scanning all data | Permanent (by design) |
| No notification for pending approvals/tasks | Users must manually check the monitor for waiting instances | Future |
| No timeout enforcement | Approval timeout is stored but not auto-enforced by scheduler | Future |
| Template usage tracking is partial | `get_template_usage()`/delete-guard only checks `stage_mappings.template_id` and flow node `config.template_id` — the dormant Campaign/Message cluster can't be checked since it isn't live | Sprint 23 (Multi-tenant) |

### Technical
| Limitation | Details |
|---|---|
| No WebSockets | Real-time updates use 10-second polling |
| Scheduler runs in-process | SchedulerService is in the same process as the API; app restart resets polling cycle |
| Single-tenant | No workspace isolation. `Template.workspace_id` exists (nullable, DB FK preserved) but nothing populates or filters by it yet |
| No caching layer | No Redis, in-memory only |
| No background workers | No Celery or task queue |
| No rate limiting | API endpoints have no throttling |
| No authentication | No user/login system (internal tool) |
| No export/import | Flows cannot be exported/imported as JSON |

## Planned Refactors

| Refactor | Priority | Notes |
|---|---|---|
| Remove `build_log_payload()` from executors | Low | Engine already creates logs |
| Remove `get_next_node_id()` from utils.py | Low | Not used by engine |
| Clean up legacy sync services | Medium | `journeys/`, `stage_mapping/`, `flows/` dirs |
| Remove `trigger_value`/`trigger_type` from journeys | Low | Legacy fields |
| Add formal test suite | High | Before production deployment |
| Graceful error for missing flow definition | Medium | User feedback instead of silent skip |
| Remove random priority in monitor | Low | Use actual data |
| Extract scheduler to separate service | Medium | For horizontal scaling and resilience |

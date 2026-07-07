# JAWCOM — Roadmap

## ✅ Completed

| Sprint | Description | Status |
|---|---|---|
| Sprint 1 | Journey Lifecycle — lead stage changed → journey match → flow definition → running instance → execution engine → execution logs | ✅ Completed |
| Sprint 2 | Executor Framework — `BaseNodeExecutor` interface, `ExecutorFactory` registry with 8 executors (Trigger, Condition, Wait, Delay, SendWhatsApp, SendEmail, Notification, End), engine refactored to dispatch via factory | ✅ Completed |
| Sprint 3 | Node Configuration System — every node exposes editable properties in the Properties Panel, configuration stored in `node.config` inside Flow Definition JSON, all 8 executors updated to read from `node.get("config")` | ✅ Completed |
| Sprint 4 | Flow Validation Engine — `FlowValidationService` with graph validation (exactly one trigger, at least one end, no orphans, all reachable, no cycles) and node validation (duration>0, required fields), `POST /{id}/validate` endpoint, Publish auto-runs validation | ✅ Completed |
| Sprint 5 | Execution Monitor & Debugger — Running Instance detail drawer with overview/timeline/logs/raw JSON tabs, execution timeline from Flow Execution Logs, node status indicators (colored dots), execution summary, search & filter, auto-refresh every 10s, disabled Retry placeholder | ✅ Completed |
| Sprint 6 | Variables Engine — `VariableResolverService` for `{{variable}}` resolution, `ExecutionContext` dataclass with resolved lead/company data, `DummyLeadProvider`, real Condition comparison engine (7 operators), variable resolution in SendWhatsApp/SendEmail/Notification executors | ✅ Completed |
| Sprint 7.5 | Architecture Refinement — `LeadProviderFactory` (registry pattern), `TemplateRendererService` (separate rendering from resolution), engine no longer instantiates `DummyLeadProvider` directly, executors use `renderer.render()` | ✅ Completed |
| Sprint 8 | Wait/Delay Scheduler — WaitExecutor pauses journey (status=waiting, resume_at), DelayExecutor stores resume_at, SchedulerService polls and resumes, engine handles skipped status | ✅ Completed |
| Sprint 9 | Retry Framework — RetryService with policy (3 retries, backoff), engine retry_node/retry_journey methods, API endpoints, frontend Retry button | ✅ Completed |
| Sprint 10 | Integration Framework — BaseIntegration interface, IntegrationFactory registry, WhatsAppIntegration (simulated) | ✅ Completed |
| Sprint 11 | Action Executors refactored — SendWhatsApp/SendEmail/Notification executors delegate to integrations, IntegrationConfig, health checks | ✅ Completed |
| Sprint 12+13 | CRM Action Framework — 6 new CRM node types, CRMIntegration, executors delegate to integrations | ✅ Completed |
| Sprint 14+15 | Human Tasks & Approval Workflow — Approval node, Manual Task node, ApprovalService, TaskService, waiting_approval/waiting_task statuses, resume framework | ✅ Completed |
| Sprint 16+17 | JAWIS Live Integration — `JawisLeadProvider`, `JawisCRMIntegration`, env-var-controlled provider switching, 6 real CRM actions | ✅ Completed |
| Sprint 18 | Template Management — consolidated on `Template`/`templates` (removed `CustomTemplate`), `/api/templates` CRUD, Flow Builder template selector for Send WhatsApp/Send Email, template_id resolution in execution | ✅ Completed |
| Sprint 19 | Journey Dashboard — Journey Summary, Execution Metrics, Recent Executions, Flow Summary, Trigger Mapping, Integration Status, Quick Actions, all computed from existing Running Instance/Flow Definition/Stage Mapping data; new `GET /api/integrations/health` | ✅ Completed |

## 🔄 In Progress

| Sprint | Description | Status |
|---|---|---|
| — | (None) | — |

## 📋 Planned

| Sprint | Description | Priority |
|---|---|---|
| Sprint 20 | Variable Filters — `{{upper(lead.name)}}`, `{{lower(...)}}`, `{{date(...)}}` | Medium |
| Sprint 21 | AI Conditions — AI-powered condition evaluation | Medium |
| Sprint 22 | Real Meta WhatsApp API — replace simulated WhatsAppIntegration | High |
| Sprint 23 | Cross-Journey Analytics — org-wide trends/comparisons across journeys (per-journey execution metrics already covered by Sprint 19's Journey Dashboard) | Low |
| Sprint 24 | Multi-tenant support (would also revive `Template.workspace_id` scoping) | Low |
| Sprint 25 | A/B testing for flows | Low |

## Future Integrations (Not Yet Scheduled)

- Webhook nodes (incoming/outgoing)
- Slack/Discord notification executors
- SMS executor (Twilio)
- Calendar/scheduling executors
- Custom script/function executors
- Export/import flows as JSON
- Version rollback and diffing
- Rate limiting and throttling

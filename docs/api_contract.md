# JAWCOM — API Contract

Base URL: `/api`

## Journey Endpoints

| Method | Path | Purpose | Request | Response |
|---|---|---|---|---|
| GET | `/journeys` | List all journeys | — | `[{id, name, description, status, trigger_type, trigger_value, flow_definition_id, created_at, updated_at}]` |
| GET | `/journeys/{id}` | Get single journey | — | Single journey object |
| POST | `/journeys` | Create journey | `{name, description?, trigger_type?, trigger_value?}` | Created journey |
| PATCH | `/journeys/{id}` | Update journey | `{name?, description?, status?, trigger_type?, trigger_value?}` | Updated journey |
| DELETE | `/journeys/{id}` | Delete journey | — | `{ok: true}` |

## Flow Definition Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/flow-definitions` | List all flow definitions |
| GET | `/flow-definitions/{id}` | Get single flow definition |
| POST | `/flow-definitions` | Create flow definition (`{name, definition: {nodes, edges}}`) |
| PATCH | `/flow-definitions/{id}` | Update flow definition |
| DELETE | `/flow-definitions/{id}` | Delete flow definition |
| POST | `/flow-definitions/{id}/publish` | Validate then publish (returns 400 if validation fails) |
| POST | `/flow-definitions/{id}/validate` | Run validation, return issues |
| POST | `/flow-definitions/{id}/create-version` | Create a new flow version snapshot |

**Validate Response (200):**
```json
{
    "valid": true,
    "issues": [],
    "summary": {"total_issues": 0, "errors": 0, "warnings": 0}
}
```

**Validate Response (200 with issues):**
```json
{
    "valid": false,
    "issues": [
        {"type": "error", "message": "...", "node_id": "...", "field": "..."},
        {"type": "warning", "message": "...", "node_id": "...", "field": "..."}
    ],
    "summary": {"total_issues": 2, "errors": 1, "warnings": 1}
}
```

## Stage Mapping Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/stage-mappings` | List all stage mappings |
| GET | `/stage-mappings/{id}` | Get single mapping |
| POST | `/stage-mappings` | Create mapping (`{journey_id, stage_key}`) |
| PATCH | `/stage-mappings/{id}` | Update mapping |
| DELETE | `/stage-mappings/{id}` | Delete mapping |

## Running Instance Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/running-instances` | List instances (supports `?journey_id=&status=&lead_id=&skip=&limit=`) |
| GET | `/running-instances/{id}` | Get single instance with full `data` JSON |
| POST | `/running-instances` | Create instance |
| PATCH | `/running-instances/{id}` | Update instance |
| DELETE | `/running-instances/{id}` | Delete instance |
| POST | `/running-instances/{id}/complete` | Mark instance as completed |
| POST | `/running-instances/{id}/fail` | Mark instance as failed |
| POST | `/running-instances/{id}/retry?mode=node\|journey` | Retry failed instance (node-level or full journey) |
| POST | `/running-instances/{id}/resume` | Resume waiting instance (skip wait/delay, continue traversal) |

**RunningInstanceSchema:**
```json
{
    "id": "uuid",
    "lead_id": 1234,
    "journey_id": "uuid",
    "current_stage_mapping_id": "uuid|null",
    "status": "running|completed|failed|waiting|waiting_approval|waiting_task",
    "started_at": "datetime",
    "completed_at": "datetime|null",
    "data": {"current_node_id": "...", "last_executed_at": "...", "trigger_stage_key": "...", "resume_at": "...", "retry_count": 0, "approvals": {...}, "tasks": {...}},
    "created_at": "datetime",
    "updated_at": "datetime"
}
```

## Execution Log Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/flow-execution-logs` | List logs (`?running_instance_id=&lead_id=&skip=&limit=`) |
| GET | `/flow-execution-logs/{id}` | Get single log |
| POST | `/flow-execution-logs` | Create log entry |
| DELETE | `/flow-execution-logs/{id}` | Delete log |

**FlowExecutionLogSchema:**
```json
{
    "id": "uuid",
    "flow_definition_id": "uuid",
    "flow_version_id": "uuid|null",
    "running_instance_id": "uuid",
    "lead_id": 1234,
    "node_id": "string (maps to flow node)",
    "status": "started|success|failed|skipped",
    "input": {"node_type": "...", "started_at": "..."},
    "output": {"completed_at": "...", "duration_ms": 123, ...},
    "error_message": "string|null",
    "executed_at": "datetime",
    "created_at": "datetime",
    "updated_at": "datetime"
}
```

## Execution Test Endpoint

| Method | Path | Purpose |
|---|---|---|
| POST | `/execution/test` | Manually trigger a journey execution |

**Request:**
```json
{
    "journey_id": "uuid",
    "lead_id": 1234,
    "stage_key": "qualified"
}
```

**Response:**
```json
{
    "success": true,
    "lead_id": 1234,
    "trigger_stage_key": "qualified",
    "journey_id": "uuid"
}
```

## Flow Version Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/flow-versions` | List versions (`?flow_definition_id=`) |
| GET | `/flow-versions/{id}` | Get single version |
| POST | `/flow-versions` | Create version snapshot |
| DELETE | `/flow-versions/{id}` | Delete version |

## Integration Architecture

External service integration is handled internally by the execution framework:

```
Executor → IntegrationFactory.get("whatsapp"|"email"|"notification")
         → integration.execute(payload)
         → provider_response stored in execution log output
```

There are no dedicated REST endpoints for individual integration *execution* — all
communication happens during node execution within a journey flow.

### Integration Health Endpoint (Sprint 19)

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/integrations/health` | Live health for WhatsApp, Email, CRM (dummy\|jawis alias), and JAWIS — used by the Journey Dashboard's Integration Status section |

**Response:**
```json
{
    "whatsapp": {"status": "unconfigured", "name": "whatsapp", "configured": false},
    "email": {"status": "unconfigured", "name": "email", "configured": false},
    "crm": {"status": "healthy", "name": "crm_dummy"},
    "jawis": {"status": "unconfigured", "name": "jawis", "configured": false, "lead_provider": "dummy", "crm_provider": "dummy"}
}
```

Each integration implements `health()` returning `{"status", "name", ...}` (this was
already true before Sprint 19 — see `BaseIntegration.health()`). This endpoint is the
first HTTP surface exposing it; no new health-check logic was added.

## Approval Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/approvals/{instance_id}` | List all approvals for an instance |
| POST | `/api/approvals/{instance_id}/{approval_id}/approve?resolved_by=` | Approve an approval (resumes journey) |
| POST | `/api/approvals/{instance_id}/{approval_id}/reject?resolved_by=` | Reject an approval (resumes journey) |

## Task Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/tasks/{instance_id}` | List all tasks for an instance |
| POST | `/api/tasks/{instance_id}/{task_id}/complete?completed_by=` | Complete a task (resumes journey) |
| POST | `/api/tasks/{instance_id}/{task_id}/reject?completed_by=` | Reject a task (resumes journey) |

## Template Endpoints (Sprint 18)

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/templates` | List templates (`?channel=email\|sms\|whatsapp\|push&status=draft\|active\|inactive`) |
| GET | `/api/templates/{id}` | Get single template |
| POST | `/api/templates` | Create template (`{name, channel, subject?, content, status?}`) |
| PATCH | `/api/templates/{id}` | Update template (`{name?, subject?, content?, channel?, status?}`) |
| DELETE | `/api/templates/{id}` | Delete template — 409 if referenced by a stage mapping or a flow node's `config.template_id` |
| POST | `/api/templates/{id}/duplicate` | Create a draft copy of a template |
| POST | `/api/templates/{id}/archive` | Set status to `inactive` |
| GET | `/api/templates/{id}/usage` | `{stage_mapping_ids, flow_definition_ids}` — everywhere this template is referenced |

**TemplateSchema:**
```json
{
    "id": "uuid",
    "name": "Welcome message",
    "channel": "whatsapp",
    "status": "draft",
    "subject": null,
    "content": "Hi {{lead.name}}, welcome!",
    "created_at": "datetime",
    "updated_at": "datetime"
}
```

Templates are consumed by `send_whatsapp`/`send_email` flow nodes via
`node.config.template_id` (set by the Flow Builder's template selector) and
resolved during execution by `SendWhatsAppExecutor`/`SendEmailExecutor`
through `exec_ctx.template_service`. The legacy free-text
`node.config.template_name` is still honored when `template_id` is absent.

## Data Model: Approvals (stored in instance.data.approvals)

```json
{
    "id": "uuid",
    "node_id": "node_1",
    "title": "Approve discount for John Doe",
    "description": "Lead has requested a 20% discount",
    "approver": "manager@company.com",
    "approval_type": "approve_reject",
    "timeout": 86400,
    "status": "pending|approved|rejected",
    "created_at": "datetime",
    "resolved_at": "datetime|null",
    "resolved_by": "string|null",
    "resolution": "string|null"
}
```

## Data Model: Tasks (stored in instance.data.tasks)

```json
{
    "id": "uuid",
    "node_id": "node_2",
    "title": "Review proposal for John Doe",
    "description": "Prepare and send a custom proposal",
    "assignee": "john.doe@company.com",
    "priority": "low|medium|high|urgent",
    "due_date": "2026-07-13",
    "status": "pending|completed|rejected",
    "created_at": "datetime",
    "completed_at": "datetime|null",
    "completed_by": "string|null"
}
```

## Future API Endpoints (Planned)

| Method | Path | Sprint |
|---|---|---|
| GET | `/execution/stats` | Sprint 16 (Analytics) |

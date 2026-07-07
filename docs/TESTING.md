# JAWCOM — Testing & QA

## Prerequisites

- Backend running: `cd backend && uvicorn app.main:app --reload`
- Frontend running: `cd frontend && npm start`
- Database: PostgreSQL with schema migrated

## Backend Startup

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # configure DATABASE_URL
uvicorn app.main:app --reload
```

## Frontend Startup

```bash
cd frontend
npm install
npm start
```

## QA Process: Full Journey Lifecycle

### 1. Create a Journey

1. Navigate to `/journeys`
2. Click "Manage Journeys" → "Create Journey"
3. Enter name (e.g., "Test Qualification Journey")
4. Click "Create"
5. Verify journey appears in the list

### 2. Create Stage Mapping

1. Click the journey to open detail view
2. Navigate to "Stage Mappings" section
3. Add a stage mapping with key (e.g., "qualified")
4. Verify mapping is saved

### 3. Build a Flow

1. Click "Open Flow Builder"
2. Verify canvas loads with ReactFlow
3. Add nodes:
   - Drag "Trigger" node onto canvas (auto-added)
   - Add "Send WhatsApp" node
   - Add "Condition" node
   - Add "Send Email" node (true branch)
   - Add "Notification" node (false branch)
   - Add "End" node
4. Connect nodes with edges
5. Configure each node's properties via the Properties Panel

### 4. Configure Node Properties

| Node | Configuration |
|---|---|
| SendWhatsApp | Template: `welcome_whatsapp`, Variables: `{"name": "{{lead.name}}"}` |
| Condition | Field: `lead.stage_key`, Operator: `equals`, Value: `qualified` |
| SendEmail (true) | Subject: `Welcome {{lead.name}} from {{company.name}}` |
| Notification (false) | Title: `Lead {{lead.name}} needs attention`, Message: `Company: {{company.name}}` |

### 5. Validate the Flow

1. Click "Validate" in the FlowToolbar
2. Verify no validation errors
3. If there are errors, fix them and validate again
4. Verify validation banner shows "Flow validation passed"

### 6. Publish the Flow

1. Click "Publish"
2. Verify success toast
3. Verify journey status changes to "ACTIVE" or flow is published

### 7. Test Execution

1. Call the test endpoint:
```bash
curl -X POST http://localhost:8000/api/execution/test \
  -H "Content-Type: application/json" \
  -d '{"journey_id": "<journey-uuid>", "lead_id": 1234, "stage_key": "qualified"}'
```

2. Verify response: `{"success": true, ...}`

### 8. Verify Execution Monitor

1. Navigate to `/journeys` (Journey Monitor view)
2. Find the running instance for lead #1234
3. Click on the row to open the detail drawer
4. **Overview tab**: verify status, current node, started/completed, duration
5. **Steps tab**: verify node status indicators (colored dots)
6. **Timeline tab**: verify chronological log entries with status badges
7. **Raw JSON tab**: verify raw data is visible

### 9. Verify Variable Resolution

1. Open the detail drawer for the executed instance
2. Check "Steps" tab — node statuses should be visible
3. Check "Timeline" tab — log entries show resolved values
4. Verify that `{{lead.name}}` was resolved to "John Doe"
5. Verify that `{{company.name}}` was resolved to "Acme Corp"

### 10. Verify Auto-Refresh

1. Keep the monitor page open
2. Run another test execution
3. Verify the new instance appears within 10 seconds (auto-refresh interval)
4. Click "Refresh" button — verify manual refresh works

### 11. Verify Condition Evaluation

1. Create a flow with a Condition node
2. Test with field value matching the condition (should take TRUE branch)
3. Test with field value NOT matching (should take FALSE branch)
4. Verify execution logs show the correct branch

## QA Process: Variable Preview (Frontend Only)

1. Open Flow Builder
2. Click on a SendWhatsApp, SendEmail, Notification, or Condition node
3. In the Properties Panel, enter a value containing `{{variable}}` (e.g., `Hello {{lead.name}}`)
4. Click the "Preview" button
5. Verify preview shows the resolved dummy value (e.g., "Hello John Doe")
6. Toggle "Hide Preview" — verify preview disappears

## QA Process: Validation

1. Create a flow with no trigger node → validate → should fail
2. Create a flow with no end node → validate → should fail
3. Create a flow with orphan nodes (not connected) → validate → should fail
4. Create a flow with a cycle → validate → should fail
5. Create a valid flow → validate → should pass
6. Try to publish an invalid flow → verify 400 error with validation issues
7. Fix all issues → publish → verify success

## QA Process: Edge Cases

- **Empty flow** (no nodes) → validation should fail
- **Flow with only trigger** → should fail (no end node)
- **Flow with multiple triggers** → should fail validation
- **Running instance for deleted journey** → monitor should handle gracefully
- **Lead with no company data** → `{{company.name}}` should remain unresolved
- **Unknown variable** → `{{unknown.field}}` should remain as-is

## QA Process: Integration Layer

### 1. Verify Integration Registry

1. Start the backend
2. Call `IntegrationFactory.registered()` (or check logs at startup)
3. Verify three integrations are registered: `whatsapp`, `email`, `notification`

### 2. Verify WhatsApp Execution Flow

1. Build a flow: Trigger → SendWhatsApp → End
2. Configure SendWhatsApp with `template_name=welcome_template`, `variables={"name": "{{lead.name}}"}`
3. Publish and execute the flow
4. Open the detail drawer → Steps tab
5. Click on the SendWhatsApp node → verify `provider_response` is in the output
6. Verify output shows `{"success": true, "provider": "whatsapp", "simulated": true}`
7. Check backend logs for "WhatsAppIntegration.execute template=..." message

### 3. Verify Email Execution Flow

1. Build a flow: Trigger → SendEmail → End
2. Configure with `subject=Hello {{lead.name}}`, `template_name=email_template`
3. Execute the flow
4. Verify `provider_response` shows `{"success": true, "provider": "email", "simulated": true}`
5. Check backend logs for "EmailIntegration.execute subject=..." message

### 4. Verify Notification Execution Flow

1. Build a flow: Trigger → Notification → End
2. Configure with `title=Alert`, `message=Lead {{lead.name}} needs attention`
3. Execute the flow
4. Verify `provider_response` shows `{"success": true, "provider": "notification", "simulated": true}`
5. Check backend logs for "NotificationIntegration.execute title=..." message

### 5. Verify Integration Health

1. Call integration health check on each integration
2. Verify all return `{"status": "unconfigured"}` (no env vars set)
3. Set `WHATSAPP_API_KEY` and `WHATSAPP_PHONE_NUMBER_ID` in `.env`
4. Call health check again → verify WhatsApp returns `{"status": "healthy", "configured": true}`

### 6. Verify IntegrationConfig

1. Check that `IntegrationConfig().to_dict()` does NOT leak secrets
2. Verify `whatsapp_api_key` value shows `"***"` instead of the actual key
- **Empty template** → renderer should return empty string

## QA Process: Wait Scheduler

### 1. Create a Flow with a Wait Node

1. Build a flow with Trigger → Wait → SendWhatsApp → End
2. Configure Wait node: duration=1, unit=minutes
3. Publish the flow
4. Test execution via the test endpoint

### 2. Verify Wait Behavior

1. Execute the flow → check that the running instance status is `waiting`
2. Verify `instance.data.resume_at` is set to ~1 minute from execution time
3. Verify execution logs show: Trigger started/success, Wait started/success (skipped)
4. Verify the instance does NOT show a log for SendWhatsApp (traversal stopped)

### 3. Verify Auto-Resume

1. Wait for the scheduler poll interval (up to 30s) after `resume_at` expires
2. Check that the instance status has transitioned to `running` or `completed`
3. Verify execution logs now show SendWhatsApp started/success, End started/success
4. Verify SendWhatsApp executed with the resolved template

### 4. Verify Manual Resume

1. Execute a flow with a Wait node (duration longer than 30s, e.g., 60 minutes)
2. While the instance is `waiting`, click on it in the monitor → open detail drawer
3. Click the "Resume" button
4. Verify instance resumes immediately (SendWhatsApp executes)

### 5. Verify Delay Node

1. Build a flow with Trigger → Delay → SendWhatsApp → End
2. Configure Delay node: duration=1, unit=minutes
3. Execute the flow
4. Verify instance status stays `running` (not `waiting`), but `data.resume_at` is set
5. After resume_at expires, verify SendWhatsApp executes

## QA Process: Retry Framework

### 1. Node-Level Retry

1. Build a flow that will fail (e.g., Trigger → Condition with invalid comparison)
2. Execute the flow
3. Verify instance status is `failed`
4. Click on the instance → open detail drawer → verify error banner shows
5. Click "Retry" button
6. Verify instance re-executes from the failed node
7. If the condition is fixed (or retry succeeds), verify instance completes

### 2. Journey-Level Retry (API)

1. Execute a flow that fails
2. Call the API: `POST /api/running-instances/{id}/retry?mode=journey`
3. Verify instance resets to the trigger node and re-executes the entire flow
4. Verify `instance.data.retry_count` increments by 1

### 3. Retry Policy Enforcement

1. Execute a flow that fails
2. Call retry 3 times (or until `max_retries` is reached)
3. Verify the 4th retry returns a 400 error: "has reached max retries"
4. Verify `instance.data.retry_count` shows exactly 3

### 4. Retry Status in Monitor

1. After a retry, open the detail drawer
2. Verify "Retry Count" MetaRow shows the retry count value
3. Verify the Steps tab shows execution logs from both the original run and the retry
4. Verify the Timeline tab shows chronological ordering of all logs

## QA Process: Human Tasks & Approval Workflow

### 1. Create a Flow with Approval + Manual Task Nodes

1. Build a flow: Trigger → ManualTask → Approval → SendEmail → End
2. Configure ManualTask: assignee=`user@company.com`, title=`Review lead {{lead.name}}`, description=`Check qualification`, priority=`high`, due_date=`2026-07-13`
3. Configure Approval: approver=`manager@company.com`, title=`Approve discount for {{lead.name}}`, description=`Lead requests 20% discount`, timeout=`86400`, approval_type=`approve_reject`
4. Configure SendEmail (to verify resume): subject=`Lead {{lead.name}} approved`, template_name=`approval_confirmed`
5. Validate → should pass (all required fields present)
6. Validate without assignee → should fail with "Manual Task requires an assignee"
7. Validate without approver → should fail with "Approval requires an approver"
8. Publish the flow

### 2. Execute and Verify Task Pause

1. Test execution via the test endpoint
2. Check that instance status is `waiting_task`
3. Verify `instance.data.tasks` contains one entry with status `pending`
4. Verify `instance.data._pause_reason` is `task`
5. Verify `instance.data.current_task_id` matches the task ID
6. Verify execution logs: Trigger started/success, ManualTask started/success (skipped)
7. Verify SendEmail does NOT appear in logs (traversal stopped at task node)

### 3. Complete Task and Verify Resume

1. Open the detail drawer → Tasks tab
2. Verify the task card shows title, description, assignee, priority, status
3. Click "Complete" button (or call `POST /api/tasks/{instance_id}/{task_id}/complete`)
4. Verify toast: "Task completed — journey resumed"
5. Verify instance status is now `running` or `completed`
6. Verify execution logs now show Approval started/success (skipped — waiting for approval)
7. Verify instance status is now `waiting_approval`

### 4. Approve and Verify Full Completion

1. Open the detail drawer → Approvals tab
2. Verify the approval card shows title, description, approver, status
3. Click "Approve" button (or call `POST /api/approvals/{instance_id}/{approval_id}/approve`)
4. Verify toast: "Approval resolved — journey resumed"
5. Verify instance status is now `running` or `completed`
6. Verify execution logs show: SendEmail started/success, End started/success
7. Verify instance status is `completed`

### 5. Verify Reject Flow

1. Build the same flow: Trigger → ManualTask → Approval → SendEmail → End
2. Execute the flow
3. Complete the task (resume to approval)
4. In the Approvals tab, click "Reject"
5. Verify the instance resumes and completes (instance.status = completed)
6. Verify SendEmail still executes (rejection does not skip downstream nodes)

### 6. Verify Retry After Rejection

1. Execute a flow with ManualTask → Approval
2. Complete the task
3. Reject the approval
4. Verify the instance completes (resume does not fail after rejection)
5. Retry should work for any `failed` instances regardless of approval/task involvement

### 8. Verify Retry After Rejection

1. Execute a flow with ManualTask → Approval
2. Complete the task
3. Reject the approval
4. Verify the instance completes (resume does not fail after rejection)
5. Retry should work for any `failed` instances regardless of approval/task involvement

### 9. Verify Execution Monitor Display

1. Create a flow with ManualTask and run it
2. In the monitor table, verify the instance shows status `waiting_task` (orange badge)
3. Click the row → open detail drawer
4. Verify "Paused For: Manual Task" in the Overview tab
5. Verify Tasks tab appears with the pending task
6. Verify Approvals tab is not shown (no approvals yet in instance data)
7. Complete the task → verify instance enters `waiting_approval`
8. Verify Approvals tab now appears with the pending approval

## QA Process: JAWIS Live Integration

### Prerequisites

- JAWIS Business OS instance with valid API credentials
- Set environment variables before starting the backend:
  ```bash
  export JAWIS_BASE_URL=https://your-jawis-instance.com
  export JAWIS_API_KEY=your-api-key
  export JAWIS_WORKSPACE=your-workspace-id
  export JAWIS_LEAD_PROVIDER=jawis
  export JAWIS_CRM_PROVIDER=jawis
  ```

### 1. Verify JAWIS LeadProvider

1. Start the backend with `JAWIS_LEAD_PROVIDER=jawis`
2. Call the test execution endpoint with a valid `lead_id` from JAWIS
3. Verify the execution context contains real lead data (name, email, phone, company)
4. Verify `{{lead.name}}` resolves to the actual lead name from JAWIS
5. Verify `{{company.name}}` resolves to the actual company name

### 2. Verify JAWIS CRM Integration — Update Lead

1. Build a flow: Trigger → UpdateLead → End
2. Configure UpdateLead with fields: `{"first_name": "Updated via Journey", "custom_field": "test_value"}`
3. Execute the flow with a real lead_id
4. Verify the JAWIS lead record is updated:
   - `first_name` changed to "Updated via Journey"
   - `custom_field` contains "test_value"
5. Check execution logs show `operation_id` and JAWIS response data

### 3. Verify JAWIS CRM Integration — Assign Owner

1. Build a flow: Trigger → AssignOwner → End
2. Configure AssignOwner with a valid `owner_id` from JAWIS
3. Execute the flow with a real lead_id
4. Verify the lead's owner is reassigned in JAWIS
5. Check `owner_id` in JAWIS matches the configured value

### 4. Verify JAWIS CRM Integration — Change Stage

1. Build a flow: Trigger → ChangeStage → End
2. Configure ChangeStage with a valid `stage_id` from JAWIS
3. Execute the flow with a real lead_id
4. Verify the lead's stage is changed in JAWIS
5. Verify execution logs show the new stage name

### 5. Verify JAWIS CRM Integration — Create Task

1. Build a flow: Trigger → CreateCRMTask → End
2. Configure CreateCRMTask with `title=Follow up with {{lead.name}}`, `description=Call lead`, `due_date=2026-07-20`
3. Execute the flow with a real lead_id
4. Verify a new task appears in JAWIS for the lead
5. Verify task title contains the resolved lead name

### 6. Verify JAWIS CRM Integration — Create Note

1. Build a flow: Trigger → CreateNote → End
2. Configure CreateNote with `content=Journey automation note for {{lead.name}}`
3. Execute the flow with a real lead_id
4. Verify a new note appears in JAWIS for the lead
5. Verify note content contains the resolved lead name

### 7. Verify Env Var Switching (Back to Dummy)

1. Restart backend with `JAWIS_LEAD_PROVIDER=dummy` and `JAWIS_CRM_PROVIDER=dummy` (or unset)
2. Execute the same flows as above
3. Verify execution logs show `simulated: true` in provider_response
4. Verify JAWIS lead record is NOT modified (data is simulated locally)

### 8. Verify Provider Registration

1. Start backend with any provider setting
2. Verify both `DummyLeadProvider` and `JawisLeadProvider` are registered in `LeadProviderFactory.registered_providers()`
3. Verify both `DummyCRMIntegration` and `JawisCRMIntegration` are registered in `IntegrationFactory.registered()`
4. Explicitly call `LeadProviderFactory.get_provider("dummy")` and verify it returns `DummyLeadProvider`
5. Explicitly call `IntegrationFactory.get("crm_dummy")` and verify it returns `DummyCRMIntegration`

### 9. Verify End-to-End Journey (Live JAWIS)

Build and execute a full journey with live JAWIS:
1. Flow: Trigger → UpdateLead → AssignOwner → ChangeStage → Wait (5min) → Approval → CreateTask → CreateNote → End
2. All CRM actions execute against real JAWIS
3. Wait pauses and resumes via scheduler
4. Approval pauses and user approves via Approvals tab
5. Task and Note are created in JAWIS after approval
6. Journey completes with all 8 nodes logged

### 10. Verify Execution Monitor Display (JAWIS Mode)

1. Execute a flow with CRM actions against live JAWIS
2. In the Steps tab, verify each CRM node shows `provider_response` with JAWIS operation details
3. Verify `simulated: true` is NOT present (confirming live execution)
4. Verify `operation_id` or API response data is visible in the output

## QA Process: Execution Monitor Display

1. Create a flow with ManualTask and run it
2. In the monitor table, verify the instance shows status `waiting_task` (orange badge)
3. Click the row → open detail drawer
4. Verify "Paused For: Manual Task" in the Overview tab
5. Verify Tasks tab appears with the pending task
6. Verify Approvals tab is not shown (no approvals yet in instance data)
7. Complete the task → verify instance enters `waiting_approval`
8. Verify Approvals tab now appears with the pending approval

"""Lightweight AI Lead Summary — GET /api/leads/{lead_id}/ai-summary.

Separate, minimal sibling of AILeadAssistantService (app/services/ai_lead_assistant_service.py):
different response shape, no fixed action vocabulary, no HTTP-error path (the
route returns {"status": "ai_unavailable"} instead). Kept as its own file so
neither AI feature can break the other.

Read-only: reuses CommunicationEventService, RunningInstanceService,
FlowExecutionLogService, and TaskService exactly as they already exist. No
new tables, no engine/webhook/provider changes, no caching, no persistence,
no automatic invocation — called only when the route is hit.
"""

import logging
from typing import Any, Dict, List
from uuid import UUID

import anthropic
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_assistant.summary_schemas import AILeadSummaryResult
from app.config.settings import get_settings
from app.services.communication_event_service import CommunicationEventService
from app.services.flow_execution_log_service import FlowExecutionLogService
from app.services.running_instance_service import RunningInstanceService
from app.services.task_service import TaskService

logger = logging.getLogger(__name__)

_MAX_EVENTS = 200
_MAX_LOGS = 200


class AIAssistantNotConfiguredError(Exception):
    """Raised when ANTHROPIC_API_KEY is not set."""


class AIAssistantProviderError(Exception):
    """Raised when the Claude API call itself fails."""


_SYSTEM_PROMPT = """You are a sales assistant embedded in a CRM communication platform. \
You are given one lead's communication events, notes, tasks, running journey \
instances, and node-level flow execution logs.

Produce exactly these fields:
1. summary: at most 6 concise bullet points covering communication events, notes, \
and tasks. Do not exceed 6.
2. journey_summary: one short paragraph summarizing journey/automation progress — \
which journeys ran, their status, and how far they got.
3. next_best_action: a short, specific recommended next action for this lead.
4. reason: a short explanation of why that action was recommended.
5. lead_health: exactly one of "Hot", "Warm", or "Cold", based on recency and \
frequency of engagement and positive/negative signals in the history.

Be concrete and specific to what actually happened for this lead — do not invent \
information that isn't in the provided context."""


def _event_line(event) -> str:
    payload = event.payload or {}
    detail = ""
    if event.event_type == "note_added":
        detail = payload.get("resolved_note") or payload.get("note") or ""
    elif event.event_type in ("whatsapp_sent", "email_sent"):
        detail = payload.get("resolved_template_name") or payload.get("template_id") or ""
    elif event.event_type in ("task_created", "task_completed"):
        detail = payload.get("title") or ""
    line = f"- [{event.occurred_at.isoformat()}] channel={event.channel} event={event.event_type}"
    if detail:
        line += f" — {detail}"
    return line


class AILeadSummaryService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._events = CommunicationEventService(session)
        self._logs = FlowExecutionLogService(session)
        self._instances = RunningInstanceService(session)
        settings = get_settings()
        self._api_key = settings.ANTHROPIC_API_KEY
        self._model = settings.ANTHROPIC_MODEL

    async def generate(self, lead_id: int) -> AILeadSummaryResult:
        if not self._api_key:
            raise AIAssistantNotConfiguredError("ANTHROPIC_API_KEY not configured")

        events = await self._events.list(lead_id=lead_id, limit=_MAX_EVENTS)
        instances = await self._instances.list(lead_id=lead_id, limit=200)
        logs = await self._logs.list(lead_id=lead_id, limit=_MAX_LOGS)

        tasks: List[Dict[str, Any]] = []
        task_service = TaskService(self._instances)
        for inst in instances:
            try:
                inst_tasks = await task_service.list_tasks(UUID(inst.id))
            except Exception:
                inst_tasks = []
            tasks.extend(inst_tasks)

        prompt = self._build_prompt(lead_id, events, instances, logs, tasks)

        client = anthropic.Anthropic(api_key=self._api_key)
        schema = AILeadSummaryResult.model_json_schema()
        schema["required"] = list(schema["properties"].keys())

        try:
            response = client.messages.create(
                model=self._model,
                max_tokens=4000,
                thinking={"type": "adaptive"},
                output_config={
                    "effort": "medium",
                    "format": {"type": "json_schema", "schema": schema},
                },
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
        except (anthropic.APIStatusError, anthropic.APIConnectionError) as exc:
            logger.error("AI Lead Summary: Claude API call failed: %s", exc)
            raise AIAssistantProviderError(str(exc)) from exc

        if response.stop_reason == "refusal":
            raise AIAssistantProviderError("Claude declined to generate a summary for this lead")

        text = next((b.text for b in response.content if b.type == "text"), None)
        if not text:
            raise AIAssistantProviderError("Claude returned no text output")

        result = AILeadSummaryResult.model_validate_json(text)
        result.summary = result.summary[:6]
        return result

    def _build_prompt(self, lead_id, events, instances, logs, tasks) -> str:
        lines: List[str] = [f"LEAD #{lead_id}", ""]

        lines.append(f"RUNNING INSTANCES ({len(instances)})")
        if not instances:
            lines.append("- none")
        for inst in instances:
            status = getattr(inst.status, "value", inst.status)
            node = (inst.data or {}).get("current_node_id") or "—"
            lines.append(f"- journey_id={inst.journey_id} status={status} current_node={node}")
        lines.append("")

        lines.append(f"FLOW EXECUTION LOGS ({len(logs)})")
        if not logs:
            lines.append("- none")
        for log in logs:
            lines.append(f"- [{log.executed_at}] node={log.node_id} status={log.status}")
        lines.append("")

        lines.append(f"TASKS ({len(tasks)})")
        if not tasks:
            lines.append("- none")
        for t in tasks:
            lines.append(f"- [{t.get('status')}] \"{t.get('title')}\" assignee={t.get('assignee') or '—'}")
        lines.append("")

        lines.append(f"COMMUNICATION EVENTS ({len(events)}, chronological)")
        if not events:
            lines.append("- none")
        for e in events:
            lines.append(_event_line(e))

        return "\n".join(lines)

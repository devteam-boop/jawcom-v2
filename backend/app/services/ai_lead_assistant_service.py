"""AI Lead Assistant — generates a per-lead summary, next-best-action
recommendation, reply suggestion, and health classification via Claude.

Reuses existing services only (CommunicationEventService, RunningInstanceService,
JourneyService, TaskService) — no new tables, no changes to the event model,
the execution engine, or any provider/integration. Purely a read + LLM-call
layer on top of what already exists.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

import anthropic
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_assistant.schemas import AILeadAssistantResult
from app.config.settings import get_settings
from app.services.communication_event_service import CommunicationEventService
from app.services.journey_service import JourneyService
from app.services.running_instance_service import RunningInstanceService
from app.services.task_service import TaskService

logger = logging.getLogger(__name__)

_MAX_EVENTS_FOR_PROMPT = 200  # keep the prompt bounded for very active leads

_SYSTEM_PROMPT = """You are a sales assistant embedded in a CRM communication platform. \
You are given the full activity history for one lead: their communication events \
(journey actions, WhatsApp/email sends, notes, task lifecycle), their journey/automation \
progress, and any open or completed tasks.

Produce exactly these four things:
1. A summary of at most 6 concise bullet points covering communication events, \
journey progress, notes, and tasks — do not exceed 6 bullets, prioritize the most \
important and recent information.
2. The single best next action for this lead, chosen from the fixed list provided, \
with a short reason.
3. A suggested reply — ONLY if the most recent communication event's channel is \
WhatsApp or email. If the latest event's channel is not WhatsApp or email (e.g. it \
is a system/journey event), leave the reply suggestion empty.
4. A lead health classification (hot, warm, or cold) based on the overall journey \
history — recency and frequency of engagement, positive signals (replies, opens, \
qualification), and negative signals (failures, long silence, no replies).

Be concrete and specific to what actually happened for this lead — do not invent \
information that isn't in the provided context."""


class AIAssistantNotConfiguredError(Exception):
    """Raised when ANTHROPIC_API_KEY is not set."""


class AIAssistantProviderError(Exception):
    """Raised when the Claude API call itself fails (network/auth/rate-limit/etc.)."""


def _event_summary_line(event) -> str:
    """One human-readable line per communication event, for the prompt digest.
    Deliberately separate from the frontend's own preview helper — this is a
    plain-text line for an LLM prompt, not a UI label."""
    payload = event.payload or {}
    detail = ""
    if event.event_type == "note_added":
        detail = payload.get("resolved_note") or payload.get("note") or ""
    elif event.event_type in ("whatsapp_sent", "email_sent"):
        detail = payload.get("resolved_template_name") or payload.get("template_id") or ""
    elif event.event_type == "condition_evaluated":
        detail = f"result={payload.get('condition_result')}"
    elif event.event_type in ("task_created", "task_completed"):
        detail = payload.get("title") or ""
    elif event.event_type == "wait_started":
        detail = f"{payload.get('duration', '')} {payload.get('unit', '')}".strip()

    line = f"- [{event.occurred_at.isoformat()}] channel={event.channel} event={event.event_type}"
    if event.provider:
        line += f" provider={event.provider}"
    if detail:
        line += f" — {detail}"
    return line


class AILeadAssistantService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._events = CommunicationEventService(session)
        self._instances = RunningInstanceService(session)
        self._journeys = JourneyService(session)
        settings = get_settings()
        self._api_key = settings.ANTHROPIC_API_KEY
        self._model = settings.ANTHROPIC_MODEL

    async def generate(self, lead_id: int) -> AILeadAssistantResult:
        if not self._api_key:
            raise AIAssistantNotConfiguredError(
                "AI Lead Assistant not configured (missing ANTHROPIC_API_KEY)"
            )

        events = await self._events.list(lead_id=lead_id, limit=_MAX_EVENTS_FOR_PROMPT)
        instances = await self._instances.list(lead_id=lead_id, limit=200)

        journey_names: Dict[str, str] = {}
        for inst in instances:
            if inst.journey_id in journey_names:
                continue
            try:
                journey = await self._journeys.get(UUID(inst.journey_id))
                journey_names[inst.journey_id] = journey.name
            except ValueError:
                journey_names[inst.journey_id] = inst.journey_id

        tasks: List[Dict[str, Any]] = []
        for inst in instances:
            try:
                task_service = TaskService(self._instances)
                inst_tasks = await task_service.list_tasks(UUID(inst.id))
            except Exception:
                inst_tasks = []
            for t in inst_tasks:
                tasks.append({**t, "journey_name": journey_names.get(inst.journey_id, inst.journey_id)})

        prompt = self._build_prompt(lead_id, events, instances, journey_names, tasks)

        client = anthropic.Anthropic(api_key=self._api_key)
        schema = AILeadAssistantResult.model_json_schema()
        schema["required"] = list(schema["properties"].keys())

        try:
            response = client.messages.create(
                model=self._model,
                max_tokens=8000,
                thinking={"type": "adaptive"},
                output_config={
                    "effort": "high",
                    "format": {"type": "json_schema", "schema": schema},
                },
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
        except anthropic.APIStatusError as exc:
            logger.error("AI Lead Assistant: Claude API error %s: %s", exc.status_code, exc.message)
            raise AIAssistantProviderError(f"Claude API error {exc.status_code}: {exc.message}") from exc
        except anthropic.APIConnectionError as exc:
            logger.error("AI Lead Assistant: Claude API unreachable: %s", exc)
            raise AIAssistantProviderError(f"Claude API unreachable: {exc}") from exc

        if response.stop_reason == "refusal":
            raise AIAssistantProviderError("Claude declined to generate a response for this lead")

        text = next((b.text for b in response.content if b.type == "text"), None)
        if not text:
            raise AIAssistantProviderError("Claude returned no text output")

        result = AILeadAssistantResult.model_validate_json(text)
        result.summary = result.summary[:6]  # defensive cap, matches the "max 6" requirement
        return result

    def _build_prompt(
        self,
        lead_id: int,
        events: list,
        instances: list,
        journey_names: Dict[str, str],
        tasks: List[Dict[str, Any]],
    ) -> str:
        lines: List[str] = [f"LEAD #{lead_id}", ""]

        lines.append(f"JOURNEYS ({len(instances)})")
        if not instances:
            lines.append("- none")
        for inst in instances:
            name = journey_names.get(inst.journey_id, inst.journey_id)
            node = (inst.data or {}).get("current_node_id") or "—"
            status = getattr(inst.status, "value", inst.status)
            lines.append(
                f"- \"{name}\" status={status} current_node={node} "
                f"started={inst.started_at} completed={inst.completed_at or '—'}"
            )
        lines.append("")

        lines.append(f"TASKS ({len(tasks)})")
        if not tasks:
            lines.append("- none")
        for t in tasks:
            lines.append(
                f"- [{t.get('status')}] \"{t.get('title')}\" journey=\"{t.get('journey_name')}\" "
                f"assignee={t.get('assignee') or '—'} priority={t.get('priority') or '—'} "
                f"due={t.get('due_date') or '—'}"
            )
        lines.append("")

        lines.append(f"COMMUNICATION TIMELINE ({len(events)} events, chronological)")
        if not events:
            lines.append("- none")
        for e in events:
            lines.append(_event_summary_line(e))
        lines.append("")

        if events:
            latest = events[-1]
            lines.append(
                f"LATEST EVENT: event_type={latest.event_type} channel={latest.channel} "
                f"occurred_at={latest.occurred_at.isoformat()}"
            )
        else:
            lines.append("LATEST EVENT: none")

        return "\n".join(lines)

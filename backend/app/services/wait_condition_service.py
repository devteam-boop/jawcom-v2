"""Wait Condition Service — evaluates event-based Wait conditions.

Given a candidate list of ``waiting`` instances paused on an event
(replied/stage_changed/field_condition — webhook_event is resolved only via
the dedicated trigger-event route, never polled here), checks each against
fresh data and returns the subset whose condition is currently satisfied.
Used by SchedulerService's poll loop alongside find_waiting()/find_due_delays
— same shared scheduling engine, no duplicate resume/traversal logic (every
due instance, regardless of which of these three found it, resumes through
the identical ExecutionEngine.resume_instance() call).
"""

import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.execution.executors.scheduling_utils import evaluate_condition
from app.execution.providers import LeadProvider, LeadProviderFactory
from app.repositories.communication_event_repository import CommunicationEventRepository
from app.runtime.schemas import RunningInstanceSchema
from app.services.running_instance_service import RunningInstanceService

logger = logging.getLogger(__name__)


async def has_replied_since(
    lead_id: int,
    channel: str,
    started_at_str: Optional[str],
    event_repo: CommunicationEventRepository,
) -> bool:
    """Single source of truth for "has this lead replied on this channel
    since a given timestamp" — used both by _is_satisfied's "replied"
    condition below (deciding an event-based Wait is due) and by
    ExecutionEngine._resume_from (telling a two-branch Wait(replied) node's
    reply branch apart from its timeout branch on resume), so neither
    caller keeps its own copy of this check.
    """
    anchor = await event_repo.get_latest_by_lead_and_event_type(lead_id, "replied", channel=channel)
    if anchor is None:
        return False
    if not started_at_str:
        return True
    try:
        started_at = datetime.fromisoformat(started_at_str)
    except ValueError:
        return True
    # Only a reply that happened AFTER this wait node started counts — a
    # stale reply from before the journey reached this node must not
    # immediately resolve it.
    return anchor.occurred_at.replace(tzinfo=None) > started_at


async def find_due_events(session: AsyncSession) -> List[RunningInstanceSchema]:
    """Return the subset of event-waiting instances whose condition is
    currently satisfied."""
    instance_service = RunningInstanceService(session)
    candidates = await instance_service.find_waiting_with_condition()
    if not candidates:
        return []

    lead_provider: LeadProvider = LeadProviderFactory.get_provider()
    event_repo = CommunicationEventRepository(session)

    due: List[RunningInstanceSchema] = []
    for inst in candidates:
        condition = (inst.data or {}).get("wait_condition") or {}
        try:
            if await _is_satisfied(condition, inst.lead_id, lead_provider, event_repo):
                due.append(inst)
        except Exception:
            logger.exception(
                "wait_condition_service: error evaluating condition for instance %s (lead=%s): %s",
                inst.id, inst.lead_id, condition,
            )
    return due


async def _is_satisfied(
    condition: dict, lead_id: int, lead_provider: LeadProvider, event_repo: CommunicationEventRepository,
) -> bool:
    condition_type = condition.get("type")

    if condition_type == "webhook_event":
        # Resolved only via POST /api/journeys/instances/{id}/trigger-event —
        # never satisfied by polling.
        return False

    if condition_type == "replied":
        channel = condition.get("channel", "whatsapp")
        started_at_str = condition.get("started_at")
        if await has_replied_since(lead_id, channel, started_at_str, event_repo):
            return True
        # No reply yet. An optional configured timeout is the only other way
        # this instance becomes due — a two-branch Wait(replied) node (see
        # ExecutionEngine._resume_from, which re-derives replied-vs-timeout
        # via the same has_replied_since() call above) uses it to fall
        # through to its timeout edge instead of waiting forever. Every
        # pre-existing "replied" Wait node has no "timeout_seconds" key at
        # all, so this always returns False here — "wait until replied,
        # however long it takes" is completely unchanged for those.
        timeout_seconds = condition.get("timeout_seconds")
        if not timeout_seconds or not started_at_str:
            return False
        try:
            started_at = datetime.fromisoformat(started_at_str)
        except ValueError:
            return False
        return (datetime.utcnow() - started_at).total_seconds() >= timeout_seconds

    if condition_type in ("stage_changed", "field_condition"):
        field = condition.get("field", "")
        operator = condition.get("operator", "equals")
        expected = condition.get("value", "")
        if not field:
            return False
        # force_refresh=True: never rely on the up-to-5-minute lead cache
        # here — a stage/field change would otherwise be detected late.
        lead_context = await lead_provider.get_lead_context(lead_id, force_refresh=True)
        lead = lead_context.get("lead") or {}
        actual = lead.get(field)
        if actual is None:
            return False
        return evaluate_condition(actual, operator, expected)

    logger.warning("wait_condition_service: unknown condition type %r", condition_type)
    return False

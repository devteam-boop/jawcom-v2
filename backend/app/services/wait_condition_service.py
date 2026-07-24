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
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.communication_event_repository import CommunicationEventRepository
from app.runtime.schemas import RunningInstanceSchema
from app.services.running_instance_service import RunningInstanceService

# app.execution.* imports are deferred (local, inside the functions that
# need them) rather than made here at module level: app.execution.__init__
# eagerly imports engine.py, which itself imports get_reply_facts/
# REPLY_FACT_FIELDS from this module — a module-level import here would
# make the two modules mutually circular, succeeding or failing purely
# based on which one happens to be imported first (fragile, order-
# dependent). Type-only references use TYPE_CHECKING so annotations still
# work without a runtime import.
if TYPE_CHECKING:
    from app.execution.providers import LeadProvider

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


# The exact keys get_reply_facts() (below) merges onto ExecutionContext's
# lead.* namespace (see ExecutionEngine._execute_for_stage/_resume_from) —
# the single source of truth for "which reply/communication facts a
# Condition node can resolve". flow_validation_service.py imports this
# constant directly (rather than keeping its own copy of these three
# strings) so its resolvable-field check can never fall out of sync with
# what the engine actually merges. The Journey Builder's Condition field
# picker (frontend/src/modules/journeys/FlowBuilder/PropertiesPanel.jsx,
# CONDITION_FIELD_OPTIONS) mirrors these same three names manually — the
# frontend/backend language boundary means it can't import this constant
# directly, same tradeoff already accepted for VARIABLE_PREVIEWS there.
REPLY_FACT_FIELDS = frozenset({"has_replied", "last_inbound_at", "replied_since_journey_start"})


async def get_reply_facts(
    lead_id: int,
    channel: str,
    journey_started_at: Optional[datetime],
    event_repo: CommunicationEventRepository,
) -> Dict[str, Any]:
    """Reply/communication facts derived from communication_events, exposed
    on ExecutionContext's lead.* namespace (see ExecutionEngine) so a
    Condition node can actually test "has the customer replied" — the only
    prior way to see a reply was the Wait node's dedicated wait_type=
    "replied" branch, which a Condition node has no access to at all.
    Reuses has_replied_since() (this module) rather than a second copy of
    the same "is there a replied event, and is it recent enough" check.

    Returns (keys == REPLY_FACT_FIELDS, asserted below):
        has_replied: a 'replied' event exists at all for this lead/channel.
        last_inbound_at: that event's occurred_at (ISO string), or None.
        replied_since_journey_start: the reply happened after
            *journey_started_at* (the running_journey_instance's own
            started_at) — None for journey_started_at skips this stricter
            check (has_replied_since already treats a missing timestamp as
            "any reply counts").
    """
    anchor = await event_repo.get_latest_by_lead_and_event_type(lead_id, "replied", channel=channel)
    facts = {
        "has_replied": anchor is not None,
        "last_inbound_at": anchor.occurred_at.isoformat() if anchor else None,
        "replied_since_journey_start": await has_replied_since(
            lead_id, channel, journey_started_at.isoformat() if journey_started_at else None, event_repo,
        ),
    }
    assert set(facts) == REPLY_FACT_FIELDS, "get_reply_facts()'s keys drifted from REPLY_FACT_FIELDS"
    return facts


async def find_due_events(session: AsyncSession) -> List[RunningInstanceSchema]:
    """Return the subset of event-waiting instances whose condition is
    currently satisfied."""
    from app.execution.providers import LeadProviderFactory  # local — see module docstring

    instance_service = RunningInstanceService(session)
    candidates = await instance_service.find_waiting_with_condition()
    if not candidates:
        return []

    lead_provider: "LeadProvider" = LeadProviderFactory.get_provider()
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
    condition: dict, lead_id: int, lead_provider: "LeadProvider", event_repo: CommunicationEventRepository,
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
        from app.execution.executors.scheduling_utils import evaluate_condition  # local — see module docstring

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

"""Shared scheduling helpers for DelayExecutor, WaitExecutor, and the
background scheduler (wait_scheduler_service.py / wait_condition_service.py).

Centralizes what used to be duplicated verbatim in delay_executor.py and
wait_executor.py (UNIT_SECONDS + duration math), plus the new lead-date/
offset resolution and condition-evaluation logic both nodes now share — one
scheduling engine, no duplicate logic.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

UNIT_SECONDS: Dict[str, int] = {
    "minutes": 60,
    "hours": 3600,
    "days": 86400,
    "weeks": 604800,
}


def apply_offset(base: datetime, value: int, unit: str) -> datetime:
    """Return ``base`` shifted by ``value`` * ``unit`` seconds.

    ``value`` may be negative (e.g. -24 hours = 24 hours *before* ``base``,
    used for "remind 24h before the tour" style Delay/Wait configs).
    """
    total_seconds = value * UNIT_SECONDS.get(unit, 60)
    return base + timedelta(seconds=total_seconds)


def parse_datetime_value(
    value: Any,
    default_tz: str = "Asia/Kolkata",
    *,
    _log_context: str = "",
) -> Optional[datetime]:
    """Parse a raw datetime value (a ``datetime``, or an ISO string as JAWIS/
    a literal config field would provide) to a naive-UTC ``datetime``, or
    ``None`` if missing/unparseable — never fabricated.

    Timezone handling: if the value already carries an explicit offset/
    timezone, it's converted to naive UTC as-is. If it's naive (no offset —
    the common case for a plain "2026-07-25T15:00:00" string), it's treated
    as already being in ``default_tz`` (JAWIS_LEAD_DATE_TIMEZONE, matching the
    frontend's existing fixed-IST display convention in
    frontend/src/lib/dateFormat.js) and converted to naive UTC from there.
    This only affects the new relative/lead-date/specific-datetime modes —
    fixed-duration Delay/Wait math is untouched and stays pure
    `now + offset` in UTC.
    """
    if value is None or value == "":
        return None

    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            logger.warning(
                "parse_datetime_value: unparseable value%s: %r",
                f" ({_log_context})" if _log_context else "", value,
            )
            return None
    else:
        return None

    if parsed.tzinfo is not None:
        return parsed.astimezone(timezone.utc).replace(tzinfo=None)

    try:
        local = parsed.replace(tzinfo=ZoneInfo(default_tz))
        return local.astimezone(timezone.utc).replace(tzinfo=None)
    except Exception:
        logger.warning(
            "parse_datetime_value: failed to localize%s value=%r to tz=%s "
            "— treating as already-UTC",
            f" ({_log_context})" if _log_context else "", value, default_tz,
        )
        return parsed


def resolve_lead_datetime_field(
    lead: Optional[Dict[str, Any]],
    field: str,
    default_tz: str = "Asia/Kolkata",
) -> Optional[datetime]:
    """Resolve a lead-owned datetime field (e.g. ``tour_datetime``,
    ``move_in_date``) to a naive-UTC ``datetime``, or ``None`` if the field
    is missing/empty/unparseable — never fabricated. See
    ``parse_datetime_value`` for the timezone-handling contract.
    """
    if not lead or not field or not isinstance(lead, dict):
        return None
    return parse_datetime_value(lead.get(field), default_tz, _log_context=f"field={field}")


def evaluate_condition(actual: Any, operator: str, expected: Any) -> bool:
    """Evaluate a field condition using the SAME comparators ConditionExecutor
    uses (imported, not reimplemented — see condition_executor.py's
    _COMPARATORS) so "wait until lead.stage == qualified" behaves identically
    to a Condition node's own equals/not_equals/greater_than/less_than/
    contains/starts_with/ends_with semantics.

    Local import to avoid a circular import at module load time (condition_
    executor.py doesn't import this module, so this is one-directional and
    safe, just deferred for import-order safety with the executors package).
    """
    from .condition_executor import _COMPARATORS

    compare_fn = _COMPARATORS.get(operator)
    if compare_fn is None:
        logger.warning("evaluate_condition: unknown operator %s", operator)
        return False
    try:
        return compare_fn(actual, expected)
    except Exception:
        logger.exception("evaluate_condition: comparison error (operator=%s)", operator)
        return False

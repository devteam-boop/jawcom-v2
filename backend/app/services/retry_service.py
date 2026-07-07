"""Retry Service — retries failed journey instances.

Supports two retry modes:
    * **Node retry** — re-execute only the failed node, then continue flow.
    * **Journey retry** — restart the entire journey from the trigger node.

Retry policy (stored in ``instance.data.retry_policy``):
    ``max_retries`` (default 3)
    ``retry_delays`` (default [60, 300, 1800] seconds — exponential backoff)
"""

import logging
from typing import Optional
from uuid import UUID

from app.execution.engine import ExecutionEngine
from app.services.running_instance_service import RunningInstanceService
from app.runtime.schemas import InstanceStatus, RunningInstanceUpdateSchema

logger = logging.getLogger(__name__)

DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAYS = [60, 300, 1800]  # 1 min, 5 min, 30 min


class RetryService:
    """Manages retry logic for failed journey instances."""

    def __init__(self, session_factory):
        self._session_factory = session_factory

    # ── Public API ─────────────────────────────────────────────────

    async def retry_node(self, instance_id: UUID) -> bool:
        """Re-execute the failed node and continue traversal.

        Increments ``instance.data.retry_count``, resets status to
        ``running``, and delegates to :meth:`ExecutionEngine.retry_node`.
        """
        return await self._do_retry(instance_id, mode="node")

    async def retry_journey(self, instance_id: UUID) -> bool:
        """Restart the entire journey from the trigger node.

        Clears ``current_node_id`` from instance data so the engine
        resolves the trigger node, then delegates to
        :meth:`ExecutionEngine.retry_journey`.
        """
        return await self._do_retry(instance_id, mode="journey")

    async def _do_retry(self, instance_id: UUID, mode: str) -> bool:
        """Shared retry logic for both modes."""
        async with self._session_factory() as session:
            instance_service = RunningInstanceService(session)
            instance = await instance_service.get(instance_id)

            if instance.status != InstanceStatus.FAILED:
                raise ValueError(
                    f"Cannot retry instance {instance_id}: "
                    f"status is {instance.status.value!r}, expected 'failed'"
                )

            # ── Enforce retry policy ────────────────────────────────
            instance_data = dict(instance.data or {})
            policy = instance_data.get("retry_policy", {})
            max_retries = policy.get("max_retries", DEFAULT_MAX_RETRIES)
            current_retry = instance_data.get("retry_count", 0)

            if current_retry >= max_retries:
                raise ValueError(
                    f"Instance {instance_id} has reached max retries "
                    f"({current_retry}/{max_retries})"
                )

            instance_data["retry_count"] = current_retry + 1

            if mode == "journey":
                instance_data["current_node_id"] = None

            await instance_service.update(
                instance_id,
                RunningInstanceUpdateSchema(
                    status=InstanceStatus.RUNNING,
                    data=instance_data,
                    completed_at=None,
                ),
            )

        # ── Execute ─────────────────────────────────────────────────
        engine = ExecutionEngine(self._session_factory)
        if mode == "node":
            return await engine.retry_node(instance_id)
        else:
            return await engine.retry_journey(instance_id)

    @staticmethod
    def compute_delay(attempt: int, delays: Optional[list] = None) -> int:
        """Return the delay in seconds for a given retry attempt.

        Uses the configured delays array if provided, else falls back
        to ``DEFAULT_RETRY_DELAYS``.  Attempts beyond the array length
        get the last value repeated.
        """
        delays = delays or DEFAULT_RETRY_DELAYS
        idx = min(attempt, len(delays)) - 1
        return delays[max(0, idx)]

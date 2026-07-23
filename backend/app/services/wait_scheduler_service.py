"""Wait Scheduler — polls for waiting instances and resumes them.

Runs as a background :mod:`asyncio` task inside the FastAPI process.
No Redis, Celery, or external scheduler is required.

Usage::

    scheduler = SchedulerService(session_factory)
    await scheduler.start()   # begins background polling loop
    ...
    await scheduler.stop()    # cancels the loop on shutdown
"""

import asyncio
import logging
from datetime import datetime
from uuid import UUID

from app.config.settings import get_settings
from app.execution.engine import ExecutionEngine

logger = logging.getLogger(__name__)


class SchedulerService:
    """Background poller that resumes waiting journey instances.

    Every *poll_interval* seconds it queries for instances with
    ``status="waiting"`` and ``data.resume_at <= now``, then passes
    each to :meth:`ExecutionEngine.resume_instance` for continuation.
    """

    def __init__(self, session_factory):
        self._session_factory = session_factory
        self._running = False
        self._task = None
        settings = get_settings()
        self._interval = settings.SCHEDULER_POLL_INTERVAL

    # ── Lifecycle ─────────────────────────────────────────────────

    async def start(self) -> None:
        """Begin the background polling loop."""
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info("SchedulerService started (interval=%ds)", self._interval)

    async def stop(self) -> None:
        """Gracefully shut down the polling loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("SchedulerService stopped")

    # ── Internal ──────────────────────────────────────────────────

    async def _poll_loop(self) -> None:
        """Continuously poll for waiting instances until stopped."""
        while self._running:
            try:
                await self._poll_once()
            except Exception as exc:
                logger.exception("Scheduler poll error: %s", exc)
            await asyncio.sleep(self._interval)

    async def _poll_once(self) -> None:
        """Find all waiting instances AND due Delay-node instances with
        expired resume_at, and resume them.

        Waiting instances (Wait/Approval/ManualTask nodes) and Delay-node
        instances are tracked differently — DelayExecutor deliberately keeps
        the instance in ``running`` status instead of transitioning it to
        ``waiting`` (see delay_executor.py), so they need a separate query
        (RunningInstanceService.find_due_delays) — find_waiting() alone never
        sees them. Both sets resume through the same
        ExecutionEngine.resume_instance() call.
        """
        from app.services.running_instance_service import RunningInstanceService
        from app.database.session import async_session_maker

        now = datetime.utcnow()
        factory = self._session_factory or async_session_maker
        async with factory() as session:
            service = RunningInstanceService(session)
            waiting_due = await service.find_waiting(now)
            delays_due = await service.find_due_delays(now)

        # TEMPORARY DIAGNOSTIC LOG — Scheduler tick (see Delay node
        # resume investigation). Fires every poll, not just when something
        # is due, so a poll interval / dead-scheduler problem is
        # distinguishable from a "nothing is due yet" one.
        logger.info(
            "Scheduler tick: current_time=%s number_of_due_delays=%d number_of_due_waits=%d",
            now.isoformat(), len(delays_due), len(waiting_due),
        )

        due = waiting_due + delays_due
        if not due:
            return

        logger.info("Scheduler found %d instance(s) to resume (%d waiting, %d delayed)",
                     len(due), len(waiting_due), len(delays_due))

        delay_instance_ids = {inst.id for inst in delays_due}

        engine = ExecutionEngine(self._session_factory)
        for inst in due:
            scheduled_time = (inst.data or {}).get("resume_at")
            node_id = (inst.data or {}).get("current_node_id")
            try:
                success = await engine.resume_instance(UUID(inst.id))
                if success:
                    logger.info("Resumed instance %s", inst.id)
                    if inst.id in delay_instance_ids:
                        # TEMPORARY DIAGNOSTIC LOG — Delay resumed.
                        actual_resume_time = datetime.utcnow()
                        logger.info(
                            "Delay resumed: lead_id=%s node_id=%s scheduled_time=%s actual_resume_time=%s",
                            inst.lead_id, node_id, scheduled_time, actual_resume_time.isoformat(),
                        )
                else:
                    logger.warning("Failed to resume instance %s", inst.id)
            except Exception as exc:
                logger.exception("Error resuming instance %s: %s", inst.id, exc)

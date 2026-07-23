"""Scheduler Engine — polls for due delays/waits and resumes them.

Runs as a background :mod:`asyncio` task inside the FastAPI process.
No Redis, Celery, or external scheduler is required.

One shared poll loop covers every pause type in the system — time-based
Wait, time-based Delay (fixed or relative-to-lead-date), and event-based
Wait (replied/stage_changed/field_condition) — each discovered by its own
query (find_waiting / find_due_delays / wait_condition_service.find_due_events)
but all resumed through the identical ExecutionEngine.resume_instance() call.
No duplicate resume/traversal logic between pause types.
(webhook_event waits are resolved only via the dedicated
POST /api/journeys/instances/{id}/trigger-event route, never polled here.)

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

    Every *poll_interval* seconds it queries for:
      - ``status="waiting"`` instances with ``data.resume_at <= now``
        (time-based Wait),
      - ``status="running"`` instances with ``data.resume_at <= now``
        (Delay — see delay_executor.py's docstring for why it stays
        "running" instead of "waiting"),
      - ``status="waiting"`` instances with a satisfied ``data.wait_condition``
        (event-based Wait — replied/stage_changed/field_condition),
    then passes each to :meth:`ExecutionEngine.resume_instance` for
    continuation.
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
        """Find every due delay/wait (time-based and event-based) and
        resume them — see the class docstring for the three queries this
        combines. Restart-safe by construction: nothing here is held in
        memory between ticks, every poll re-queries from the database, so a
        server restart loses no pending resume."""
        from app.services.running_instance_service import RunningInstanceService
        from app.services import wait_condition_service
        from app.database.session import async_session_maker

        now = datetime.utcnow()
        factory = self._session_factory or async_session_maker
        async with factory() as session:
            service = RunningInstanceService(session)
            waiting_due = await service.find_waiting(now)
            delays_due = await service.find_due_delays(now)
            events_due = await wait_condition_service.find_due_events(session)

        # Scheduler tick — permanent structured log, not just a debug
        # aid: fires every poll (not only when something is due) so a dead
        # scheduler / bad poll interval is distinguishable from "nothing due
        # yet" purely from the logs (requirement: "Detailed execution logs
        # for scheduling and resume").
        logger.info(
            "Scheduler tick: current_time=%s number_of_due_delays=%d "
            "number_of_due_waits=%d number_of_due_events=%d",
            now.isoformat(), len(delays_due), len(waiting_due), len(events_due),
        )

        due = waiting_due + delays_due + events_due
        if not due:
            return

        logger.info(
            "Scheduler found %d instance(s) to resume (%d waiting, %d delayed, %d event)",
            len(due), len(waiting_due), len(delays_due), len(events_due),
        )

        delay_instance_ids = {inst.id for inst in delays_due}
        event_instance_ids = {inst.id for inst in events_due}

        engine = ExecutionEngine(self._session_factory)
        for inst in due:
            scheduled_time = (inst.data or {}).get("resume_at")
            wait_condition = (inst.data or {}).get("wait_condition")
            node_id = (inst.data or {}).get("current_node_id")
            try:
                success = await engine.resume_instance(UUID(inst.id))
                if success:
                    logger.info("Resumed instance %s", inst.id)
                    actual_resume_time = datetime.utcnow()
                    if inst.id in delay_instance_ids:
                        logger.info(
                            "Delay resumed: lead_id=%s node_id=%s scheduled_time=%s actual_resume_time=%s",
                            inst.lead_id, node_id, scheduled_time, actual_resume_time.isoformat(),
                        )
                    elif inst.id in event_instance_ids:
                        logger.info(
                            "Event wait resumed: lead_id=%s node_id=%s wait_condition=%s actual_resume_time=%s",
                            inst.lead_id, node_id, wait_condition, actual_resume_time.isoformat(),
                        )
                else:
                    logger.warning("Failed to resume instance %s", inst.id)
            except Exception as exc:
                logger.exception("Error resuming instance %s: %s", inst.id, exc)

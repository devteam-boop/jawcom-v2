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
        """Find all waiting instances with expired resume_at and resume them."""
        from app.services.running_instance_service import RunningInstanceService
        from app.database.session import async_session_maker

        factory = self._session_factory or async_session_maker
        async with factory() as session:
            service = RunningInstanceService(session)
            due = await service.find_waiting(datetime.utcnow())

        if not due:
            return

        logger.info("Scheduler found %d waiting instance(s) to resume", len(due))

        engine = ExecutionEngine(self._session_factory)
        for inst in due:
            try:
                success = await engine.resume_instance(UUID(inst.id))
                if success:
                    logger.info("Resumed instance %s", inst.id)
                else:
                    logger.warning("Failed to resume instance %s", inst.id)
            except Exception as exc:
                logger.exception("Error resuming instance %s: %s", inst.id, exc)

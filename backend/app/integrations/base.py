"""Abstract base for all external-service integrations.

Every integration (WhatsApp, Email, Slack, CRM, …) implements this interface.
Executors never call third‑party APIs directly — they build a request payload
and delegate to ``integration.execute()``.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseIntegration(ABC):
    """Interface every external‑service adapter must implement.

    Minimal required methods: ``name`` (property), ``execute``.
    Optional lifecycle hooks: ``connect``, ``disconnect``, ``health``.
    """

    # ── Identity ───────────────────────────────────────────────────

    @property
    @abstractmethod
    def name(self) -> str:
        """Logical name e.g. ``"whatsapp"``, ``"email"``."""
        ...

    # ── Lifecycle hooks (optional, default no‑op) ──────────────────

    async def connect(self) -> bool:
        """Establish a connection to the external service.

        Called once before the first ``execute()``.
        Default: no‑op, returns ``True``.
        """
        return True

    async def disconnect(self) -> bool:
        """Tear down the connection gracefully.

        Called on application shutdown or when the integration is
        no longer needed.  Default: no‑op, returns ``True``.
        """
        return True

    # ── Health / introspection ─────────────────────────────────────

    async def health(self) -> Dict[str, Any]:
        """Return current health status.

        Shape::

            {"status": "healthy" | "unhealthy" | "error",
             "name": self.name,
             ...integration‑specific fields}
        """
        return {"status": "healthy", "name": self.name}

    # ── Execution ──────────────────────────────────────────────────

    @abstractmethod
    async def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the integration with the given *payload*.

        Args:
            payload: Service‑specific payload built by the executor
                     (e.g. template name, variables, recipient).

        Returns:
            A dict containing at least ``"success": bool`` and
            service‑specific result data.
        """
        ...

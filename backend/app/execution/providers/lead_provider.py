"""Lead Provider abstraction — interface + factory for lead/company runtime data.

Provides a clean seam between the execution engine and JAWIS data source.
The engine works exclusively via ``LeadProvider`` and ``LeadProviderFactory``
so it never hard-codes a concrete provider.
"""

import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type


class LeadProvider(ABC):
    """Abstract interface for fetching lead context data.

    Implementations must return a dict with the shape::

        {
            "lead": {
                "id": int | str,
                "name": str,
                "email": str | None,
                "phone": str | None,
                "stage_key": str | None,
            },
            "company": {
                "id": int | str | None,
                "name": str | None,
                "industry": str | None,
                "size": str | None,
            } | None,
        }
    """

    @abstractmethod
    async def get_lead_context(self, lead_id: int, force_refresh: bool = False) -> Dict[str, Any]:
        """``force_refresh``: bypass any provider-level cache (JawisLeadProvider's
        underlying JawisClient caches for 5 minutes) — used by
        wait_condition_service.py when polling for a stage/field change, so
        a change is never missed for up to 5 minutes. Every other existing
        caller passes the default (False), unchanged behavior."""
        ...


class DummyLeadProvider(LeadProvider):
    """Returns hardcoded dummy data — no external dependency.

    Swap for ``JawisLeadProvider`` (future) when JAWIS is available.
    """

    async def get_lead_context(self, lead_id: int, force_refresh: bool = False) -> Dict[str, Any]:
        return {
            "lead": {
                "id": lead_id,
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "+1234567890",
                "stage_key": "qualification",
                # Additive dummy values for the JAWIS notification variable
                # set (see SendWhatsAppExecutor) — lets local/manual
                # verification exercise the full success path without a
                # live JAWIS connection. Mirrors the full standardized
                # 18-field variable contract for parity with
                # JawisLeadProvider (see that class for the live equivalent).
                "city": "Lucknow",
                "first_name": "John",
                "last_name": "Doe",
                "company": "Acme Corp",
                "building_name": "Acme Business Tower",
                "building_id": "BLD-1042",
                "agent_name": "Jane Agent",
                "assigned_to": "Jane Agent",
                "seats": "2",
                "options_link": "https://example.com/options/42",
                "tour_datetime": "2026-08-01 11:00 AM",
                "map_link": "https://maps.example.com/acme-tower",
                "plan_type": "2BHK",
                "proposal_link": "https://example.com/proposal/42",
                "price": "1.2Cr",
                "move_in_date": "2026-09-15",
            },
            "company": {
                "id": 1,
                "name": "Acme Corp",
                "industry": "Technology",
                "size": "50-200",
                "website": "https://acme.example.com",
            },
        }


class LeadProviderFactory:
    """Registry-based factory for ``LeadProvider`` implementations.

    Usage::

        provider = LeadProviderFactory.get_provider("dummy")
        context = await provider.get_lead_context(42)

    Register new providers without modifying factory code::

        LeadProviderFactory.register("jawis", JawisLeadProvider)
    """

    _registry: Dict[str, Type[LeadProvider]] = {}

    @classmethod
    def register(cls, name: str, provider_cls: Type[LeadProvider]) -> None:
        """Register a provider class under a logical name."""
        cls._registry[name] = provider_cls

    @classmethod
    def get_provider(cls, name: Optional[str] = None) -> LeadProvider:
        """Return an instance of the registered provider.

        When *name* is ``None``, reads the ``JAWIS_LEAD_PROVIDER``
        environment variable (default: ``"dummy"``).  Allows switching
        providers by configuration without touching any code.

        Raises ``ValueError`` when *name* is not registered.
        """
        if name is None:
            name = os.environ.get("JAWIS_LEAD_PROVIDER", "dummy")
        provider_cls = cls._registry.get(name)
        if provider_cls is None:
            raise ValueError(
                f"Unknown lead provider {name!r}. "
                f"Registered: {list(cls._registry)}"
            )
        return provider_cls()

    @classmethod
    def registered_providers(cls) -> Dict[str, str]:
        """Return ``{name: class_qualname}`` for introspection."""
        return {n: c.__name__ for n, c in cls._registry.items()}


# ── Auto-register built-in providers ─────────────────────────────────
LeadProviderFactory.register("dummy", DummyLeadProvider)

# JAWISLeadProvider is registered lazily on first import to avoid
# circular imports (it depends on app.jawis.client).
from .jawis_lead_provider import JawisLeadProvider  # noqa: E402
LeadProviderFactory.register("jawis", JawisLeadProvider)

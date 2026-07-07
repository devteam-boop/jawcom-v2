"""Registry‑based factory for ``BaseIntegration`` implementations.

Usage::

    integration = IntegrationFactory.get("whatsapp")
    result = await integration.execute(payload)
    health = await integration.health()

New integrations are registered without modifying factory code::

    IntegrationFactory.register("slack", SlackIntegration)
"""

import os
from typing import Dict, Type

from .base import BaseIntegration


class IntegrationFactory:
    """Registry for ``BaseIntegration`` subclasses.

    Follows the same registry pattern as ``LeadProviderFactory`` and
    ``ExecutorFactory``.

    The special key ``"crm"`` is resolved based on the
    ``JAWIS_CRM_PROVIDER`` environment variable: when set to ``"jawis"``
    the factory returns ``JawisCRMIntegration``, otherwise the
    ``DummyCRMIntegration``.  This allows switching CRM backends by
    configuration without touching any executor code.
    """

    _registry: Dict[str, Type[BaseIntegration]] = {}
    _ALIASES: Dict[str, str] = {}

    @classmethod
    def register(cls, name: str, integration_cls: Type[BaseIntegration]) -> None:
        """Register an integration class under a logical *name*."""
        cls._registry[name] = integration_cls

    @classmethod
    def register_alias(cls, alias: str, target_name: str) -> None:
        """Register *alias* → *target_name* resolution.

        When ``get(alias)`` is called, it resolves to the integration
        registered under *target_name* instead.
        """
        cls._ALIASES[alias] = target_name

    @classmethod
    def get(cls, name: str) -> BaseIntegration:
        """Return an instance of the registered integration.

        Supports aliases: ``"crm"`` resolves to the backend configured
        via ``JAWIS_CRM_PROVIDER``.

        Raises ``ValueError`` when *name* is not registered.
        """
        # Resolve aliases
        if name in cls._ALIASES:
            name = cls._ALIASES[name]

        integration_cls = cls._registry.get(name)
        if integration_cls is None:
            raise ValueError(
                f"Unknown integration {name!r}. "
                f"Registered: {list(cls._registry)}"
            )
        return integration_cls()

    @classmethod
    def registered(cls) -> Dict[str, str]:
        """Return ``{name: class_qualname}`` for introspection."""
        return {n: c.__name__ for n, c in cls._registry.items()}


# ── Set up the "crm" alias based on JAWIS_CRM_PROVIDER env var ────────
_crm_backend = os.environ.get("JAWIS_CRM_PROVIDER", "dummy")
if _crm_backend == "jawis":
    IntegrationFactory.register_alias("crm", "crm_jawis")
else:
    IntegrationFactory.register_alias("crm", "crm_dummy")

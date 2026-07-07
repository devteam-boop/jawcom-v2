"""Integrations package — pluggable external-service adapters.

Every external service (WhatsApp, Email, Slack, CRM, …) is wrapped in a
:class:`BaseIntegration` subclass registered with :class:`IntegrationFactory`.
Executors never call third-party APIs directly; they build a request payload
and delegate execution to ``integration.execute()``.
"""

from .base import BaseIntegration
from .factory import IntegrationFactory
from .config import IntegrationConfig
from .whatsapp import WhatsAppIntegration
from .email import EmailIntegration
from .notification import NotificationIntegration
from .crm import DummyCRMIntegration
from .jawis_crm import JawisCRMIntegration
from .jawis_communication import (
    JawisCommunicationIntegration,
    JawisWhatsAppIntegration,
    JawisEmailIntegration,
)

# Auto-register built‑in integrations
IntegrationFactory.register("whatsapp", JawisWhatsAppIntegration)
IntegrationFactory.register("email", JawisEmailIntegration)
IntegrationFactory.register("whatsapp_dummy", WhatsAppIntegration)
IntegrationFactory.register("email_dummy", EmailIntegration)
IntegrationFactory.register("notification", NotificationIntegration)
IntegrationFactory.register("crm_dummy", DummyCRMIntegration)
IntegrationFactory.register("crm_jawis", JawisCRMIntegration)

__all__ = [
    "BaseIntegration",
    "IntegrationFactory",
    "IntegrationConfig",
    "WhatsAppIntegration",
    "EmailIntegration",
    "NotificationIntegration",
    "DummyCRMIntegration",
    "JawisCRMIntegration",
    "JawisCommunicationIntegration",
    "JawisWhatsAppIntegration",
    "JawisEmailIntegration",
]

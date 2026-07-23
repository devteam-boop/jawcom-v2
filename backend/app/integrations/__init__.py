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
from .jawis_notification import JawisNotificationIntegration
from .crm import DummyCRMIntegration
from .jawis_crm import JawisCRMIntegration
from .jawis_communication import (
    JawisCommunicationIntegration,
    JawisWhatsAppIntegration,
    JawisEmailIntegration,
)
from .native_providers import (
    NativeProviderError,
    MetaWhatsAppIntegration,
    ResendEmailIntegration,
)

# Auto-register built‑in integrations.
# "whatsapp"/"email"/"notification" are no longer registered directly —
# like "crm", they are now pure aliases (see factory.py) resolved by
# JAWIS_WHATSAPP_PROVIDER / JAWIS_EMAIL_PROVIDER / JAWIS_NOTIFICATION_PROVIDER,
# defaulting to "jawis" so the Journey Builder's Notification node now really
# calls JAWIS by default. JawisWhatsAppIntegration.name/JawisEmailIntegration.name/
# JawisNotificationIntegration.name still report "whatsapp"/"email"/
# "notification" (unchanged) so the default /api/integrations/health response
# is unaffected by this registry key rename.
IntegrationFactory.register("whatsapp_jawis", JawisWhatsAppIntegration)
IntegrationFactory.register("email_jawis", JawisEmailIntegration)
IntegrationFactory.register("whatsapp_dummy", WhatsAppIntegration)
IntegrationFactory.register("email_dummy", EmailIntegration)
IntegrationFactory.register("whatsapp_meta", MetaWhatsAppIntegration)
IntegrationFactory.register("email_resend", ResendEmailIntegration)
IntegrationFactory.register("notification_jawis", JawisNotificationIntegration)
IntegrationFactory.register("notification_dummy", NotificationIntegration)
IntegrationFactory.register("crm_dummy", DummyCRMIntegration)
IntegrationFactory.register("crm_jawis", JawisCRMIntegration)

__all__ = [
    "BaseIntegration",
    "IntegrationFactory",
    "IntegrationConfig",
    "WhatsAppIntegration",
    "EmailIntegration",
    "NotificationIntegration",
    "JawisNotificationIntegration",
    "DummyCRMIntegration",
    "JawisCRMIntegration",
    "JawisCommunicationIntegration",
    "JawisWhatsAppIntegration",
    "JawisEmailIntegration",
    "NativeProviderError",
    "MetaWhatsAppIntegration",
    "ResendEmailIntegration",
]

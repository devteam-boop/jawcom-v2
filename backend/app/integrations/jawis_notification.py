"""JAWIS Notification integration — posts Notification-node payloads to JAWIS.

Reuses ``JawisCommunicationIntegration`` (jawis_communication.py) for the
actual HTTP request/response/error handling (same bearer-auth convention as
the WhatsApp/Email JAWIS integrations) — only ``name``/``_endpoint`` differ.
Same ADR-017 contract: raises ``JawisCommunicationError`` on failure so the
existing engine exception handler marks the node/instance Failed with no
executor/engine change required.

Retrying before giving up is handled by the caller (NotificationExecutor),
not here — this class performs exactly one HTTP attempt per call, same as
JawisWhatsAppIntegration/JawisEmailIntegration.
"""

from .config import IntegrationConfig
from .jawis_communication import JawisCommunicationIntegration


class JawisNotificationIntegration(JawisCommunicationIntegration):
    """Sends a Notification-node payload via JAWIS's notification API.

    Endpoint path is configurable (``JAWIS_NOTIFICATION_ENDPOINT``, default
    ``/api/notifications/send``, following the same ``/api/messages/
    {channel}/send`` convention as the Sprint-1 messaging endpoints) — verify
    it against JAWIS's real API contract and adjust via env var if needed,
    no code change required.
    """

    @property
    def name(self) -> str:
        return "notification"

    @property
    def _endpoint(self) -> str:
        return IntegrationConfig().jawis_notification_endpoint

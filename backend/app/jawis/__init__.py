"""JAWIS integration module for JawCom."""

from .client import JawisClient, JawisApiError, get_jawis_client, close_jawis_client
from .webhook import JawisWebhookHandler, get_webhook_handler
from .schemas import (
    LeadSchema,
    CompanySchema,
    StageSchema,
    UserSchema,
    LeadContextSchema,
    WebhookEventSchema,
    WebhookResponseSchema,
    JawisApiResponse
)

__all__ = [
    # Client
    "JawisClient",
    "JawisApiError",
    "get_jawis_client",
    "close_jawis_client",
    
    # Webhook
    "JawisWebhookHandler",
    "get_webhook_handler",
    
    # Schemas
    "LeadSchema",
    "CompanySchema",
    "StageSchema",
    "UserSchema",
    "LeadContextSchema",
    "WebhookEventSchema",
    "WebhookResponseSchema",
    "JawisApiResponse"
]

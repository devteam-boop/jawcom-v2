"""
JawCom Provider Abstraction Layer

This module provides a clean abstraction for communication providers,
allowing JawCom to support multiple WhatsApp and Email providers
without changing business logic.

Usage:
    from app.providers import provider_registry, Channel
    from app.providers.meta import MetaProvider
    from app.providers.resend import ResendProvider
    
    # Register providers
    provider_registry.register_provider(
        Channel.WHATSAPP, 
        MetaProvider, 
        {"access_token": "...", "phone_number_id": "..."}
    )
    
    provider_registry.register_provider(
        Channel.EMAIL,
        ResendProvider,
        {"api_key": "...", "from_email": "..."}
    )
    
    # Use providers
    whatsapp = provider_registry.get_whatsapp_provider()
    email = provider_registry.get_email_provider()
"""

from .registry.provider_registry import provider_registry, Channel
from .base.communication_provider import CommunicationProvider, MessageStatus, MessageType
from .base.whatsapp_provider import WhatsAppProvider
from .base.email_provider import EmailProvider
from .meta.meta_provider import MetaProvider
from .resend.resend_provider import ResendProvider

__all__ = [
    "provider_registry",
    "Channel",
    "CommunicationProvider",
    "MessageStatus", 
    "MessageType",
    "WhatsAppProvider",
    "EmailProvider",
    "MetaProvider",
    "ResendProvider"
]

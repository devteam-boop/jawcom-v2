from typing import Dict, Type, Optional
from enum import Enum
from ..base.communication_provider import CommunicationProvider
from ..base.whatsapp_provider import WhatsAppProvider
from ..base.email_provider import EmailProvider


class Channel(Enum):
    """Communication channels supported by JawCom."""
    WHATSAPP = "whatsapp"
    EMAIL = "email"


class ProviderRegistry:
    """Registry for managing communication providers by channel."""
    
    def __init__(self):
        """Initialize empty provider registry."""
        self._providers: Dict[Channel, Type[CommunicationProvider]] = {}
        self._instances: Dict[Channel, CommunicationProvider] = {}
        self._configs: Dict[Channel, Dict] = {}
    
    def register_provider(
        self,
        channel: Channel,
        provider_class: Type[CommunicationProvider],
        config: Optional[Dict] = None
    ) -> None:
        """
        Register a provider for a specific channel.
        
        Args:
            channel: Communication channel
            provider_class: Provider class to register
            config: Provider configuration
        """
        self._providers[channel] = provider_class
        if config:
            self._configs[channel] = config
    
    def get_provider(self, channel: Channel) -> Optional[CommunicationProvider]:
        """
        Get provider instance for a channel.
        
        Args:
            channel: Communication channel
            
        Returns:
            Provider instance or None if not registered
        """
        if channel not in self._providers:
            return None
        
        # Return cached instance if exists
        if channel in self._instances:
            return self._instances[channel]
        
        # Create new instance
        provider_class = self._providers[channel]
        config = self._configs.get(channel, {})
        
        try:
            instance = provider_class(config)
            self._instances[channel] = instance
            return instance
        except Exception as e:
            # Log error in production
            print(f"Failed to create provider for {channel}: {e}")
            return None
    
    def get_whatsapp_provider(self) -> Optional[WhatsAppProvider]:
        """
        Get WhatsApp provider instance.
        
        Returns:
            WhatsApp provider or None if not registered
        """
        provider = self.get_provider(Channel.WHATSAPP)
        if isinstance(provider, WhatsAppProvider):
            return provider
        return None
    
    def get_email_provider(self) -> Optional[EmailProvider]:
        """
        Get Email provider instance.
        
        Returns:
            Email provider or None if not registered
        """
        provider = self.get_provider(Channel.EMAIL)
        if isinstance(provider, EmailProvider):
            return provider
        return None
    
    def is_channel_configured(self, channel: Channel) -> bool:
        """
        Check if a channel has a configured provider.
        
        Args:
            channel: Communication channel
            
        Returns:
            True if channel is configured
        """
        provider = self.get_provider(channel)
        return provider is not None and provider.is_configured()
    
    def get_configured_channels(self) -> list[Channel]:
        """
        Get list of all configured channels.
        
        Returns:
            List of configured channels
        """
        return [
            channel for channel in Channel
            if self.is_channel_configured(channel)
        ]
    
    def unregister_provider(self, channel: Channel) -> None:
        """
        Unregister provider for a channel.
        
        Args:
            channel: Communication channel
        """
        self._providers.pop(channel, None)
        self._instances.pop(channel, None)
        self._configs.pop(channel, None)


# Global provider registry instance
provider_registry = ProviderRegistry()

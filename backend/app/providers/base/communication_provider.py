from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum


class MessageStatus(Enum):
    """Message delivery status."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class MessageType(Enum):
    """Message content type."""
    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"
    TEMPLATE = "template"


class CommunicationProvider(ABC):
    """Abstract base class for all communication providers."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize provider with configuration."""
        self.config = config
        self.provider_name = self.__class__.__name__
    
    @abstractmethod
    async def send_message(
        self,
        recipient: str,
        message: str,
        message_type: MessageType = MessageType.TEXT,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a message to recipient.
        
        Args:
            recipient: Recipient identifier (phone/email)
            message: Message content
            message_type: Type of message content
            metadata: Additional provider-specific data
            
        Returns:
            Dict containing provider message ID and status
        """
        pass
    
    @abstractmethod
    async def get_message_status(self, provider_message_id: str) -> MessageStatus:
        """
        Get delivery status of a message.
        
        Args:
            provider_message_id: Provider's message identifier
            
        Returns:
            Current message status
        """
        pass
    
    @abstractmethod
    async def validate_recipient(self, recipient: str) -> bool:
        """
        Validate if recipient is reachable via this provider.
        
        Args:
            recipient: Recipient identifier
            
        Returns:
            True if recipient is valid
        """
        pass
    
    @abstractmethod
    def get_supported_message_types(self) -> list[MessageType]:
        """
        Get list of message types supported by this provider.
        
        Returns:
            List of supported MessageType enums
        """
        pass
    
    def get_provider_name(self) -> str:
        """Get the provider name."""
        return self.provider_name
    
    def is_configured(self) -> bool:
        """Check if provider is properly configured."""
        return bool(self.config)

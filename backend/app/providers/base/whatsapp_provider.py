from abc import abstractmethod
from typing import Dict, Any, Optional, List
from .communication_provider import CommunicationProvider, MessageType


class WhatsAppProvider(CommunicationProvider):
    """Abstract base class for WhatsApp providers."""
    
    @abstractmethod
    async def send_template_message(
        self,
        recipient: str,
        template_name: str,
        template_language: str,
        template_parameters: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send a WhatsApp template message.
        
        Args:
            recipient: Phone number in international format
            template_name: Approved template name
            template_language: Template language code (e.g., 'en_US')
            template_parameters: List of parameter values for template
            
        Returns:
            Dict containing provider message ID and status
        """
        pass
    
    @abstractmethod
    async def get_template_status(self, template_name: str) -> str:
        """
        Get approval status of a WhatsApp template.
        
        Args:
            template_name: Template name to check
            
        Returns:
            Template status (APPROVED, PENDING, REJECTED)
        """
        pass
    
    @abstractmethod
    async def upload_media(self, media_url: str, media_type: str) -> str:
        """
        Upload media to WhatsApp and get media ID.
        
        Args:
            media_url: URL of media to upload
            media_type: Type of media (image, document, etc.)
            
        Returns:
            WhatsApp media ID
        """
        pass
    
    def get_supported_message_types(self) -> List[MessageType]:
        """WhatsApp supports text, image, document, and template messages."""
        return [
            MessageType.TEXT,
            MessageType.IMAGE,
            MessageType.DOCUMENT,
            MessageType.TEMPLATE
        ]
    
    async def validate_recipient(self, recipient: str) -> bool:
        """
        Validate WhatsApp phone number format.
        
        Args:
            recipient: Phone number to validate
            
        Returns:
            True if phone number format is valid
        """
        # Basic validation - should be international format without +
        if not recipient.isdigit():
            return False
        
        # Should be between 10-15 digits
        if len(recipient) < 10 or len(recipient) > 15:
            return False
            
        return True

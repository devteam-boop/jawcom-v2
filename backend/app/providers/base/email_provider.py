from abc import abstractmethod
from typing import Dict, Any, Optional, List
import re
from .communication_provider import CommunicationProvider, MessageType


class EmailProvider(CommunicationProvider):
    """Abstract base class for Email providers."""
    
    @abstractmethod
    async def send_email(
        self,
        recipient: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Send an email message.
        
        Args:
            recipient: Email address
            subject: Email subject line
            body: Plain text email body
            html_body: HTML email body (optional)
            attachments: List of attachment dicts with 'filename' and 'content'
            
        Returns:
            Dict containing provider message ID and status
        """
        pass
    
    @abstractmethod
    async def send_template_email(
        self,
        recipient: str,
        template_id: str,
        template_variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send an email using a provider template.
        
        Args:
            recipient: Email address
            template_id: Provider template identifier
            template_variables: Variables to substitute in template
            
        Returns:
            Dict containing provider message ID and status
        """
        pass
    
    @abstractmethod
    async def get_bounce_status(self, provider_message_id: str) -> Optional[str]:
        """
        Get bounce/complaint status for an email.
        
        Args:
            provider_message_id: Provider's message identifier
            
        Returns:
            Bounce reason if bounced, None if delivered successfully
        """
        pass
    
    def get_supported_message_types(self) -> List[MessageType]:
        """Email supports text and document messages."""
        return [
            MessageType.TEXT,
            MessageType.DOCUMENT
        ]
    
    async def validate_recipient(self, recipient: str) -> bool:
        """
        Validate email address format.
        
        Args:
            recipient: Email address to validate
            
        Returns:
            True if email format is valid
        """
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, recipient))

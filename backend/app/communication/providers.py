"""Provider implementations for sending messages."""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class WhatsAppProvider:
    """Mock WhatsApp provider for sending messages."""
    
    def send_message(self, recipient: str, content: str, template_id: str) -> Dict[str, Any]:
        """
        Send WhatsApp message (mock implementation).
        
        Args:
            recipient: Recipient phone number
            content: Message content
            template_id: Template ID used
            
        Returns:
            Send result
        """
        try:
            # Log the message send (this is our success criteria)
            logger.info(f"WhatsApp Template Sent - Template: {template_id}, Recipient: {recipient}")
            
            return {
                "success": True,
                "message": "WhatsApp Template Sent",
                "provider": "whatsapp",
                "recipient": recipient,
                "template_id": template_id
            }
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {str(e)}")
            return {
                "success": False,
                "message": f"Error sending WhatsApp message: {str(e)}",
                "provider": "whatsapp"
            }

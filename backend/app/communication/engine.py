"""Communication engine for sending messages via providers."""

from typing import Dict, Any
from ..templates.services import TemplateService
from ..templates.renderer import TemplateRenderer
import logging

logger = logging.getLogger(__name__)


class CommunicationEngine:
    """Engine for sending messages via various providers."""
    
    def __init__(self, template_service: TemplateService):
        """Initialize communication engine."""
        self.template_service = template_service
        self.renderer = TemplateRenderer()
    
    def send_message(self, template_id: str, recipient: str, 
                    variables: Dict[str, Any], channel: str) -> Dict[str, Any]:
        """
        Send message using template and variables.
        
        Args:
            template_id: Template ID
            recipient: Recipient identifier
            variables: Template variables
            channel: Communication channel
            
        Returns:
            Send result
        """
        try:
            # Get template
            template = self.template_service.get_template(template_id)
            
            # Render template
            rendered_content = self.template_service.render_template(
                {"template_id": template_id, "variables": variables}
            )
            
            # Send via appropriate provider
            if channel == "whatsapp":
                from .providers import WhatsAppProvider
                provider = WhatsAppProvider()
                result = provider.send_message(
                    recipient, 
                    rendered_content, 
                    template_id
                )
                logger.info("WhatsApp Template Sent")
                return result
            else:
                raise ValueError(f"Unsupported channel: {channel}")
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return {
                "success": False,
                "message": f"Error sending message: {str(e)}"
            }

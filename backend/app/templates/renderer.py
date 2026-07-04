"""Template rendering engine."""

import re
from typing import Dict, Any, Optional, List
from jinja2 import Template, Environment, StrictUndefined
from .exceptions import TemplateValidationError


class TemplateRenderer:
    """Renderer for template content with variable substitution."""
    
    VARIABLE_PATTERN = r"\{\{(\w+)\}\}"
    
    def __init__(self):
        """Initialize template renderer with strict environment."""
        self.env = Environment(
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    def render(self, content: str, variables: Dict[str, Any]) -> str:
        """
        Render template content with provided variables.
        
        Args:
            content: Template content with variables
            variables: Dictionary of variable names and values
            
        Returns:
            Rendered content with variables substituted
            
        Raises:
            TemplateValidationError: If variables are missing or invalid
        """
        # Validate that all required variables are provided
        required_vars = self._extract_variables(content)
        missing_vars = [var for var in required_vars if var not in variables]
        
        if missing_vars:
            raise TemplateValidationError(f"Missing required variables: {missing_vars}")
        
        # Render template using Jinja2
        try:
            template = self.env.from_string(content)
            return template.render(**variables)
        except Exception as e:
            raise TemplateValidationError(f"Template rendering failed: {str(e)}")
    
    def render_email(self, subject: str, content: str, variables: Dict[str, Any]) -> Dict[str, str]:
        """
        Render email template with subject and content.
        
        Args:
            subject: Email subject template
            content: Email content template
            variables: Dictionary of variable names and values
            
        Returns:
            Dictionary with rendered subject and content
        """
        return {
            "subject": self.render(subject, variables),
            "content": self.render(content, variables)
        }
    
    def render_whatsapp(self, content: str, variables: Dict[str, Any]) -> str:
        """
        Render WhatsApp template content.
        
        Args:
            content: WhatsApp content template
            variables: Dictionary of variable names and values
            
        Returns:
            Rendered WhatsApp content
        """
        return self.render(content, variables)
    
    def _extract_variables(self, content: str) -> List[str]:
        """Extract variable names from template content."""
        matches = re.findall(self.VARIABLE_PATTERN, content)
        return list(set(matches))  # Remove duplicates

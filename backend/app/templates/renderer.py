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
    
    # Meta's numbered placeholder convention ({{1}}, {{2}}, ...) — distinct
    # from this class's own Jinja2 {{name}} convention (VARIABLE_PATTERN
    # above). Root cause of WhatsApp sends rendering "Hello 1," instead of
    # "Hello Shivansh,": Jinja2 parses a bare digit inside {{ }} as an
    # INTEGER LITERAL expression, not a variable-name lookup — {{1}} always
    # evaluated to the literal 1 via self.render() below, regardless of
    # what `variables` contained. Mirrors the proven-correct substitution
    # already used for Meta-synced templates (see _render_meta_text in
    # app/whatsapp_templates/service.py) rather than reusing that private
    # function directly, to avoid a cross-module dependency for one regex.
    _NUMBERED_VARIABLE_PATTERN = re.compile(r"\{\{\s*(\d+)\s*\}\}")

    def render_whatsapp(self, content: str, variables: Dict[str, Any]) -> str:
        """
        Render WhatsApp template content.

        Supports two variable conventions that both flow through this one
        method today: Meta's numbered {{1}}/{{2}} placeholders (looked up
        as string keys, e.g. {"1": "Shivansh"} — substituted directly via
        regex below, NOT through Jinja2) and this renderer's own {{name}}
        Jinja2 placeholders (any remaining {{...}} tokens after the
        numbered pass, handled by self.render() exactly as before — email/
        generic-table templates using {{name}} are unaffected).

        Args:
            content: WhatsApp content template
            variables: Dictionary of variable names and values

        Returns:
            Rendered WhatsApp content
        """
        def _substitute_numbered(match: "re.Match") -> str:
            key = match.group(1)
            # Lenient on a genuinely missing key (leaves {{1}} as-is rather
            # than raising) — matches _render_meta_text's behavior for the
            # same case.
            return str(variables[key]) if key in variables else match.group(0)

        content = self._NUMBERED_VARIABLE_PATTERN.sub(_substitute_numbered, content)
        return self.render(content, variables)
    
    def _extract_variables(self, content: str) -> List[str]:
        """Extract variable names from template content."""
        matches = re.findall(self.VARIABLE_PATTERN, content)
        return list(set(matches))  # Remove duplicates

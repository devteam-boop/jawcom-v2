"""Template validation utilities."""

import re
from typing import List, Set
from .exceptions import TemplateValidationError


class TemplateValidator:
    """Validator for template content and structure."""

    VARIABLE_PATTERN = r"\{\{(\w+)\}\}"
    
    @classmethod
    def validate_template_content(cls, content: str, channel: str) -> List[str]:
        """
        Validate template content and return list of variables.
        
        Args:
            content: Template content with variables
            channel: Template channel (email, whatsapp)
            
        Returns:
            List of variable names found in template
            
        Raises:
            TemplateValidationError: If validation fails
        """
        variables = cls._extract_variables(content)
        
        # Check for duplicate variables
        if len(variables) != len(set(variables)):
            duplicates = [var for var in set(variables) if variables.count(var) > 1]
            raise TemplateValidationError(f"Duplicate variables found: {duplicates}")
        
        # Check for invalid syntax
        if not cls._is_valid_syntax(content):
            raise TemplateValidationError("Invalid template syntax detected")
            
        return variables
    
    @classmethod
    def validate_email_template(cls, subject: str, content: str) -> None:
        """
        Validate email template specific requirements.
        
        Args:
            subject: Email subject line
            content: Email content
            
        Raises:
            TemplateValidationError: If validation fails
        """
        if not subject or not subject.strip():
            raise TemplateValidationError("Email template must have a subject")
    
    @classmethod
    def validate_template_name(cls, name: str) -> None:
        """
        Validate template name.
        
        Args:
            name: Template name
            
        Raises:
            TemplateValidationError: If validation fails
        """
        if not name or not name.strip():
            raise TemplateValidationError("Template name cannot be empty")
        
        if len(name) > 255:
            raise TemplateValidationError("Template name too long (max 255 characters)")
    
    @classmethod
    def _extract_variables(cls, content: str) -> List[str]:
        """Extract variable names from template content."""
        matches = re.findall(cls.VARIABLE_PATTERN, content)
        return matches
    
    @classmethod
    def _is_valid_syntax(cls, content: str) -> bool:
        """Check if template syntax is valid."""
        # Check for unmatched opening braces
        open_braces = content.count("{{")
        close_braces = content.count("}}")
        
        if open_braces != close_braces:
            return False
            
        # Check for empty variables
        if "{{}}" in content:
            return False
            
        # Check for invalid characters in variable names
        variables = cls._extract_variables(content)
        for var in variables:
            if not re.match(r"^[a-zA-Z_]\w*$", var):
                return False
                
        return True

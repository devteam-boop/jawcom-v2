"""Custom exceptions for the Template Engine."""


class TemplateEngineError(Exception):
    """Base exception for Template Engine errors."""
    pass


class TemplateNotFoundError(TemplateEngineError):
    """Raised when a template is not found."""
    pass


class TemplateValidationError(TemplateEngineError):
    """Raised when template validation fails."""
    pass


class TemplateInUseError(TemplateEngineError):
    """Raised when trying to delete a template that is in use."""
    pass

"""Custom exceptions for WhatsApp Template Management (Phase 1)."""


class WhatsAppTemplateError(Exception):
    """Base exception for WhatsApp Template Management errors."""
    pass


class WhatsAppTemplateNotFoundError(WhatsAppTemplateError):
    """Raised when a WhatsApp template is not found."""
    pass


class WhatsAppTemplateNotApprovedError(WhatsAppTemplateError):
    """Raised when a send is attempted against a template Meta hasn't approved."""
    pass


class MetaSyncError(WhatsAppTemplateError):
    """Raised when the Meta Cloud API list-templates call itself fails."""
    pass

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


class MetaSubmissionError(WhatsAppTemplateError):
    """Raised when Meta rejects a template creation submission (Phase 3) —
    carries Meta's real error message verbatim; status must stay DRAFT."""
    pass


class WhatsAppTemplateInvalidStateError(WhatsAppTemplateError):
    """Raised when an action is attempted against a template in the wrong
    state (e.g. submitting a template that isn't DRAFT)."""
    pass

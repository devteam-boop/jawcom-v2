"""Custom exceptions for the Journey Engine."""


class JourneyEngineError(Exception):
    """Base exception for Journey Engine errors."""
    pass


class JourneyNotFoundError(JourneyEngineError):
    """Raised when a journey is not found."""
    pass


class JourneyValidationError(JourneyEngineError):
    """Raised when journey validation fails."""
    pass


class JourneyActivationError(JourneyEngineError):
    """Raised when journey activation fails."""
    pass


class InvalidJourneyStateError(JourneyEngineError):
    """Raised when journey state is invalid for the requested operation."""
    pass

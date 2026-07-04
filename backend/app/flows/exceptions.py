"""Custom exceptions for the Flow Definition Engine."""


class FlowEngineError(Exception):
    """Base exception for Flow Engine errors."""
    pass


class FlowValidationError(FlowEngineError):
    """Raised when flow validation fails."""
    pass


class FlowPublishError(FlowEngineError):
    """Raised when flow publishing fails."""
    pass


class FlowVersionError(FlowEngineError):
    """Raised when flow versioning operations fail."""
    pass


class InvalidNodeError(FlowEngineError):
    """Raised when a node definition is invalid."""
    pass

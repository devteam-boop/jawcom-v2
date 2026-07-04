"""Custom exceptions for the Running Journey Instance Engine."""


class RunningInstanceError(Exception):
    """Base exception for Running Instance Engine errors."""
    pass


class RunningInstanceNotFoundError(RunningInstanceError):
    """Raised when a running instance is not found."""
    pass


class DuplicateRunningInstanceError(RunningInstanceError):
    """Raised when trying to create a duplicate running instance."""
    pass


class InvalidInstanceStateError(RunningInstanceError):
    """Raised when instance state is invalid for the requested operation."""
    pass


class RunningInstanceValidationError(RunningInstanceError):
    """Raised when running instance validation fails."""
    pass

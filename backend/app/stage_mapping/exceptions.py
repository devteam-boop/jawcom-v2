"""Custom exceptions for the Stage Mapping Engine."""


class StageMappingError(Exception):
    """Base exception for Stage Mapping Engine errors."""
    pass


class StageMappingNotFoundError(StageMappingError):
    """Raised when a stage mapping is not found."""
    pass


class StageMappingValidationError(StageMappingError):
    """Raised when stage mapping validation fails."""
    pass


class DuplicateStageMappingError(StageMappingError):
    """Raised when trying to create a duplicate stage mapping."""
    pass


class InvalidTriggerError(StageMappingError):
    """Raised when trigger configuration is invalid."""
    pass

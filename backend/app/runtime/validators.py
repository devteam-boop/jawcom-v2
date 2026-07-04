"""Running Instance validation utilities."""

from sqlalchemy.orm import Session
from .schemas import RunningInstanceCreateSchema
from .exceptions import (
    RunningInstanceValidationError, 
    DuplicateRunningInstanceError
)
from ..models import RunningJourneyInstance, Journey
from ..journeys.schemas import JourneyStatus


class RunningInstanceValidator:
    """Validator for running instance structure and content."""

    def __init__(self, db_session: Session):
        """Initialize running instance validator."""
        self.db = db_session

    def validate_instance_creation(self, instance_data: RunningInstanceCreateSchema) -> None:
        """
        Validate running instance creation data.
        
        Args:
            instance_data: Running instance creation data
            
        Raises:
            RunningInstanceValidationError: If validation fails
        """
        self._validate_lead_journey_combination(instance_data.lead_id, instance_data.journey_id)
        self._validate_journey_active(instance_data.journey_id)
        self._validate_flow_published(instance_data.flow_id)

    def _validate_lead_journey_combination(self, lead_id: str, journey_id: str) -> None:
        """Validate that lead+journey combination is unique."""
        existing_instance = self.db.query(RunningJourneyInstance).filter(
            RunningJourneyInstance.lead_id == lead_id,
            RunningJourneyInstance.journey_id == journey_id,
            RunningJourneyInstance.status.in_(["created", "running", "waiting", "paused"])
        ).first()
        
        if existing_instance:
            raise DuplicateRunningInstanceError(
                f"Active instance already exists for lead {lead_id} and journey {journey_id}"
            )

    def _validate_journey_active(self, journey_id: str) -> None:
        """Validate that journey is active."""
        journey = self.db.query(Journey).filter(Journey.id == journey_id).first()
        if not journey:
            raise RunningInstanceValidationError(f"Journey {journey_id} not found")
        
        if journey.status != JourneyStatus.ACTIVE.value:
            raise RunningInstanceValidationError("Journey must be active to create running instance")

    def _validate_flow_published(self, flow_id: str) -> None:
        """Validate that flow is published."""
        # In a real implementation, this would check the flow status
        # For now, we'll assume the flow service handles this validation
        pass

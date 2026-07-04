"""Journey management utilities."""

from typing import List, Optional
from sqlalchemy.orm import Session
from .schemas import (
    JourneySchema,
    JourneyCreateSchema,
    JourneyUpdateSchema,
    JourneyStatus
)
from .exceptions import JourneyNotFoundError, InvalidJourneyStateError
from ..models import Journey as JourneyModel


class JourneyManager:
    """Helper class for managing journeys."""

    def __init__(self, db_session: Session):
        """Initialize journey manager."""
        self.db = db_session

    def activate_journey(self, journey_id: str) -> JourneySchema:
        """
        Activate a journey.
        
        Args:
            journey_id: Journey ID
            
        Returns:
            Updated journey schema
            
        Raises:
            JourneyNotFoundError: If journey not found
            InvalidJourneyStateError: If journey cannot be activated
        """
        journey = self.db.query(JourneyModel).filter(JourneyModel.id == journey_id).first()
        if not journey:
            raise JourneyNotFoundError(f"Journey {journey_id} not found")
        
        if journey.status == JourneyStatus.ACTIVE:
            raise InvalidJourneyStateError("Journey is already active")
            
        if journey.status == JourneyStatus.ARCHIVED:
            raise InvalidJourneyStateError("Cannot activate archived journey")
        
        journey.status = JourneyStatus.ACTIVE.value
        self.db.commit()
        self.db.refresh(journey)
        
        return self._model_to_schema(journey)

    def pause_journey(self, journey_id: str) -> JourneySchema:
        """
        Pause a journey.
        
        Args:
            journey_id: Journey ID
            
        Returns:
            Updated journey schema
            
        Raises:
            JourneyNotFoundError: If journey not found
            InvalidJourneyStateError: If journey cannot be paused
        """
        journey = self.db.query(JourneyModel).filter(JourneyModel.id == journey_id).first()
        if not journey:
            raise JourneyNotFoundError(f"Journey {journey_id} not found")
        
        if journey.status != JourneyStatus.ACTIVE:
            raise InvalidJourneyStateError("Only active journeys can be paused")
        
        journey.status = JourneyStatus.PAUSED.value
        self.db.commit()
        self.db.refresh(journey)
        
        return self._model_to_schema(journey)

    def archive_journey(self, journey_id: str) -> JourneySchema:
        """
        Archive a journey.
        
        Args:
            journey_id: Journey ID
            
        Returns:
            Updated journey schema
            
        Raises:
            JourneyNotFoundError: If journey not found
        """
        journey = self.db.query(JourneyModel).filter(JourneyModel.id == journey_id).first()
        if not journey:
            raise JourneyNotFoundError(f"Journey {journey_id} not found")
        
        journey.status = JourneyStatus.ARCHIVED.value
        self.db.commit()
        self.db.refresh(journey)
        
        return self._model_to_schema(journey)

    def get_active_journeys(self, workspace_id: str) -> List[JourneySchema]:
        """
        Get all active journeys for a workspace.
        
        Args:
            workspace_id: Workspace ID
            
        Returns:
            List of active journey schemas
        """
        journeys = self.db.query(JourneyModel).filter(
            JourneyModel.workspace_id == workspace_id,
            JourneyModel.status == JourneyStatus.ACTIVE.value
        ).all()
        
        return [self._model_to_schema(journey) for journey in journeys]

    def get_journeys_by_trigger(self, workspace_id: str, trigger_type: str, 
                               trigger_value: Optional[str] = None) -> List[JourneySchema]:
        """
        Get journeys by trigger type and value.
        
        Args:
            workspace_id: Workspace ID
            trigger_type: Trigger type
            trigger_value: Trigger value (optional)
            
        Returns:
            List of journey schemas
        """
        query = self.db.query(JourneyModel).filter(
            JourneyModel.workspace_id == workspace_id,
            JourneyModel.trigger_type == trigger_type
        )
        
        if trigger_value:
            query = query.filter(JourneyModel.trigger_value == trigger_value)
            
        journeys = query.all()
        return [self._model_to_schema(journey) for journey in journeys]

    def _model_to_schema(self, journey: JourneyModel) -> JourneySchema:
        """Convert journey model to schema."""
        from .schemas import BusinessHoursSchema, RetryPolicySchema
        
        business_hours = None
        if journey.business_hours:
            business_hours = BusinessHoursSchema(**journey.business_hours)
            
        retry_policy = None
        if journey.retry_policy:
            retry_policy = RetryPolicySchema(**journey.retry_policy)
        
        return JourneySchema(
            id=str(journey.id),
            name=journey.name,
            description=journey.description,
            status=journey.status,
            flow_id=str(journey.flow_id),
            trigger_type=journey.trigger_type,
            trigger_value=journey.trigger_value,
            automation_enabled=journey.automation_enabled,
            priority=journey.priority,
            business_hours=business_hours,
            retry_policy=retry_policy,
            created_at=journey.created_at,
            updated_at=journey.updated_at,
            workspace_id=str(journey.workspace_id)
        )

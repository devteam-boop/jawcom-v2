"""Journey Engine services."""

from typing import List, Optional
from datetime import datetime
import uuid
from sqlalchemy.orm import Session
from .schemas import (
    JourneySchema,
    JourneyCreateSchema,
    JourneyUpdateSchema,
    JourneyStatus
)
from .validators import JourneyValidator
from .journey_manager import JourneyManager
from .exceptions import (
    JourneyNotFoundError,
    JourneyValidationError,
    InvalidJourneyStateError
)
from ..models import Journey as JourneyModel
from ..flows.services import FlowService


class JourneyService:
    """Service for managing journeys."""
    
    def __init__(self, db_session: Session, flow_service: FlowService):
        """Initialize journey service."""
        self.db = db_session
        self.flow_service = flow_service
        self.validator = JourneyValidator(db_session)
        self.manager = JourneyManager(db_session)
    
    def create_journey(self, journey_data: JourneyCreateSchema) -> JourneySchema:
        """
        Create a new journey.
        
        Args:
            journey_data: Journey creation data
            
        Returns:
            Created journey schema
            
        Raises:
            JourneyValidationError: If validation fails
        """
        # Validate journey data
        self.validator.validate_journey_creation(journey_data)
        
        # Create journey model
        journey = JourneyModel(
            id=uuid.uuid4(),
            name=journey_data.name,
            description=journey_data.description,
            status=JourneyStatus.DRAFT.value,
            flow_id=journey_data.flow_id,
            trigger_type=journey_data.trigger_type.value,
            trigger_value=journey_data.trigger_value,
            automation_enabled=journey_data.automation_enabled,
            priority=journey_data.priority,
            business_hours=journey_data.business_hours.dict() if journey_data.business_hours else None,
            retry_policy=journey_data.retry_policy.dict() if journey_data.retry_policy else None,
            workspace_id=journey_data.workspace_id
        )
        
        self.db.add(journey)
        self.db.commit()
        self.db.refresh(journey)
        
        return self._model_to_schema(journey)
    
    def get_journey(self, journey_id: str) -> JourneySchema:
        """
        Get journey by ID.
        
        Args:
            journey_id: Journey ID
            
        Returns:
            Journey schema
            
        Raises:
            JourneyNotFoundError: If journey not found
        """
        journey = self.db.query(JourneyModel).filter(JourneyModel.id == journey_id).first()
        if not journey:
            raise JourneyNotFoundError(f"Journey {journey_id} not found")
        
        return self._model_to_schema(journey)
    
    def update_journey(self, journey_id: str, update_data: JourneyUpdateSchema) -> JourneySchema:
        """
        Update journey.
        
        Args:
            journey_id: Journey ID
            update_data: Update data
            
        Returns:
            Updated journey schema
            
        Raises:
            JourneyNotFoundError: If journey not found
            JourneyValidationError: If validation fails
        """
        journey = self.db.query(JourneyModel).filter(JourneyModel.id == journey_id).first()
        if not journey:
            raise JourneyNotFoundError(f"Journey {journey_id} not found")
        
        # Validate update data
        self.validator.validate_journey_update(journey_id, update_data)
        
        # Update fields if provided
        if update_data.name is not None:
            journey.name = update_data.name
            
        if update_data.description is not None:
            journey.description = update_data.description
            
        if update_data.status is not None:
            journey.status = update_data.status.value
            
        if update_data.flow_id is not None:
            journey.flow_id = update_data.flow_id
            
        if update_data.trigger_type is not None:
            journey.trigger_type = update_data.trigger_type.value
            
        if update_data.trigger_value is not None:
            journey.trigger_value = update_data.trigger_value
            
        if update_data.automation_enabled is not None:
            journey.automation_enabled = update_data.automation_enabled
            
        if update_data.priority is not None:
            journey.priority = update_data.priority
            
        if update_data.business_hours is not None:
            journey.business_hours = update_data.business_hours.dict() if update_data.business_hours else None
            
        if update_data.retry_policy is not None:
            journey.retry_policy = update_data.retry_policy.dict() if update_data.retry_policy else None
        
        journey.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(journey)
        
        return self._model_to_schema(journey)
    
    def delete_journey(self, journey_id: str) -> bool:
        """
        Delete journey.
        
        Args:
            journey_id: Journey ID
            
        Returns:
            True if deleted
            
        Raises:
            JourneyNotFoundError: If journey not found
        """
        journey = self.db.query(JourneyModel).filter(JourneyModel.id == journey_id).first()
        if not journey:
            raise JourneyNotFoundError(f"Journey {journey_id} not found")
        
        self.db.delete(journey)
        self.db.commit()
        return True
    
    def list_journeys(self, workspace_id: str, status: Optional[str] = None) -> List[JourneySchema]:
        """
        List journeys for a workspace.
        
        Args:
            workspace_id: Workspace ID
            status: Optional status filter
            
        Returns:
            List of journey schemas
        """
        query = self.db.query(JourneyModel).filter(JourneyModel.workspace_id == workspace_id)
        
        if status:
            query = query.filter(JourneyModel.status == status)
            
        journeys = query.all()
        return [self._model_to_schema(journey) for journey in journeys]
    
    def activate_journey(self, journey_id: str) -> JourneySchema:
        """
        Activate a journey.
        
        Args:
            journey_id: Journey ID
            
        Returns:
            Updated journey schema
        """
        return self.manager.activate_journey(journey_id)
    
    def pause_journey(self, journey_id: str) -> JourneySchema:
        """
        Pause a journey.
        
        Args:
            journey_id: Journey ID
            
        Returns:
            Updated journey schema
        """
        return self.manager.pause_journey(journey_id)
    
    def archive_journey(self, journey_id: str) -> JourneySchema:
        """
        Archive a journey.
        
        Args:
            journey_id: Journey ID
            
        Returns:
            Updated journey schema
        """
        return self.manager.archive_journey(journey_id)
    
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

"""Journey validation utilities."""

from typing import List
from sqlalchemy.orm import Session
from .schemas import JourneyCreateSchema, JourneyUpdateSchema, TriggerType
from .exceptions import JourneyValidationError
from ..models import Journey, FlowDefinition
from ..flows.schemas import FlowStatus


class JourneyValidator:
    """Validator for journey structure and content."""

    def __init__(self, db_session: Session):
        """Initialize journey validator."""
        self.db = db_session

    def validate_journey_creation(self, journey_data: JourneyCreateSchema) -> None:
        """
        Validate journey creation data.
        
        Args:
            journey_data: Journey creation data
            
        Raises:
            JourneyValidationError: If validation fails
        """
        self._validate_journey_name(journey_data.name)
        self._validate_flow_reference(journey_data.flow_id)
        self._validate_trigger(journey_data.trigger_type, journey_data.trigger_value)
        self._validate_unique_trigger_priority(
            journey_data.workspace_id,
            journey_data.trigger_type,
            journey_data.trigger_value,
            journey_data.priority
        )

    def validate_journey_update(self, journey_id: str, update_data: JourneyUpdateSchema) -> None:
        """
        Validate journey update data.
        
        Args:
            journey_id: Journey ID
            update_data: Journey update data
            
        Raises:
            JourneyValidationError: If validation fails
        """
        if update_data.name is not None:
            self._validate_journey_name(update_data.name)
            
        if update_data.flow_id is not None:
            self._validate_flow_reference(update_data.flow_id)
            
        if update_data.trigger_type is not None or update_data.trigger_value is not None:
            trigger_type = update_data.trigger_type
            trigger_value = update_data.trigger_value
            
            # If only one is updated, get the other from existing journey
            if trigger_type is None or trigger_value is None:
                existing_journey = self.db.query(Journey).filter(Journey.id == journey_id).first()
                if not existing_journey:
                    raise JourneyValidationError(f"Journey {journey_id} not found")
                    
                if trigger_type is None:
                    trigger_type = existing_journey.trigger_type
                if trigger_value is None:
                    trigger_value = existing_journey.trigger_value
                    
            self._validate_trigger(trigger_type, trigger_value)
            
        # Check for duplicate trigger+priority if either is being updated
        if (update_data.trigger_type is not None or 
            update_data.trigger_value is not None or 
            update_data.priority is not None):
            
            existing_journey = self.db.query(Journey).filter(Journey.id == journey_id).first()
            if not existing_journey:
                raise JourneyValidationError(f"Journey {journey_id} not found")
                
            workspace_id = existing_journey.workspace_id
            trigger_type = update_data.trigger_type or existing_journey.trigger_type
            trigger_value = update_data.trigger_value or existing_journey.trigger_value
            priority = update_data.priority or existing_journey.priority
            
            self._validate_unique_trigger_priority(
                workspace_id, trigger_type, trigger_value, priority, journey_id
            )

    def _validate_journey_name(self, name: str) -> None:
        """Validate journey name."""
        if not name or not name.strip():
            raise JourneyValidationError("Journey name cannot be empty")
        
        if len(name) > 255:
            raise JourneyValidationError("Journey name too long (max 255 characters)")

    def _validate_flow_reference(self, flow_id: str) -> None:
        """Validate that flow reference is valid and published."""
        flow = self.db.query(FlowDefinition).filter(FlowDefinition.id == flow_id).first()
        if not flow:
            raise JourneyValidationError(f"Flow {flow_id} not found")
        
        if flow.status != FlowStatus.PUBLISHED.value:
            raise JourneyValidationError("Journey must reference a published flow")

    def _validate_trigger(self, trigger_type: TriggerType, trigger_value: str) -> None:
        """Validate trigger configuration."""
        if not trigger_type:
            raise JourneyValidationError("Trigger type is required")
            
        # Validate trigger value based on trigger type
        if trigger_type == TriggerType.LEAD_STAGE_CHANGED and not trigger_value:
            raise JourneyValidationError("Trigger value is required for lead stage changed trigger")
        
        if trigger_type not in list(TriggerType):
            raise JourneyValidationError(f"Invalid trigger type: {trigger_type}")

    def _validate_unique_trigger_priority(self, workspace_id: str, trigger_type: TriggerType, 
                                        trigger_value: str, priority: int, 
                                        exclude_journey_id: str = None) -> None:
        """Validate that no other active journey has the same trigger+priority combination."""
        query = self.db.query(Journey).filter(
            Journey.workspace_id == workspace_id,
            Journey.trigger_type == trigger_type,
            Journey.priority == priority,
            Journey.status == "active"
        )
        
        if trigger_type == TriggerType.LEAD_STAGE_CHANGED:
            query = query.filter(Journey.trigger_value == trigger_value)
            
        if exclude_journey_id:
            query = query.filter(Journey.id != exclude_journey_id)
            
        existing_journey = query.first()
        if existing_journey:
            raise JourneyValidationError(
                f"An active journey with the same trigger and priority already exists: {existing_journey.name}"
            )

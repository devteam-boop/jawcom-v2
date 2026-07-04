"""Stage Mapping validation utilities."""

from sqlalchemy.orm import Session
from .schemas import StageMappingCreateSchema, StageMappingUpdateSchema, TriggerType
from .exceptions import StageMappingValidationError, DuplicateStageMappingError, InvalidTriggerError
from ..models import StageMapping, Journey
from ..journeys.schemas import JourneyStatus


class StageMappingValidator:
    """Validator for stage mapping structure and content."""

    def __init__(self, db_session: Session):
        """Initialize stage mapping validator."""
        self.db = db_session

    def validate_mapping_creation(self, mapping_data: StageMappingCreateSchema) -> None:
        """
        Validate stage mapping creation data.
        
        Args:
            mapping_data: Stage mapping creation data
            
        Raises:
            StageMappingValidationError: If validation fails
        """
        self._validate_mapping_name(mapping_data.name)
        self._validate_journey_reference(mapping_data.journey_id)
        self._validate_trigger(mapping_data.trigger_type, mapping_data.trigger_value)
        self._validate_unique_trigger_priority(
            mapping_data.workspace_id,
            mapping_data.trigger_type,
            mapping_data.trigger_value,
            mapping_data.priority
        )

    def validate_mapping_update(self, mapping_id: str, update_data: StageMappingUpdateSchema) -> None:
        """
        Validate stage mapping update data.
        
        Args:
            mapping_id: Stage mapping ID
            update_data: Stage mapping update data
            
        Raises:
            StageMappingValidationError: If validation fails
        """
        if update_data.name is not None:
            self._validate_mapping_name(update_data.name)
            
        if update_data.journey_id is not None:
            self._validate_journey_reference(update_data.journey_id)
            
        if update_data.trigger_type is not None or update_data.trigger_value is not None:
            trigger_type = update_data.trigger_type
            trigger_value = update_data.trigger_value
            
            # If only one is updated, get the other from existing mapping
            if trigger_type is None or trigger_value is None:
                existing_mapping = self.db.query(StageMapping).filter(StageMapping.id == mapping_id).first()
                if not existing_mapping:
                    raise StageMappingValidationError(f"Stage mapping {mapping_id} not found")
                    
                if trigger_type is None:
                    trigger_type = existing_mapping.trigger_type
                if trigger_value is None:
                    trigger_value = existing_mapping.trigger_value
                    
            self._validate_trigger(trigger_type, trigger_value)
            
        # Check for duplicate trigger+priority if either is being updated
        if (update_data.trigger_type is not None or 
            update_data.trigger_value is not None or 
            update_data.priority is not None):
            
            existing_mapping = self.db.query(StageMapping).filter(StageMapping.id == mapping_id).first()
            if not existing_mapping:
                raise StageMappingValidationError(f"Stage mapping {mapping_id} not found")
                
            workspace_id = existing_mapping.workspace_id
            trigger_type = update_data.trigger_type or existing_mapping.trigger_type
            trigger_value = update_data.trigger_value or existing_mapping.trigger_value
            priority = update_data.priority or existing_mapping.priority
            
            self._validate_unique_trigger_priority(
                workspace_id, trigger_type, trigger_value, priority, mapping_id
            )

    def _validate_mapping_name(self, name: str) -> None:
        """Validate stage mapping name."""
        if not name or not name.strip():
            raise StageMappingValidationError("Stage mapping name cannot be empty")
        
        if len(name) > 255:
            raise StageMappingValidationError("Stage mapping name too long (max 255 characters)")

    def _validate_journey_reference(self, journey_id: str) -> None:
        """Validate that journey reference is valid and active."""
        journey = self.db.query(Journey).filter(Journey.id == journey_id).first()
        if not journey:
            raise StageMappingValidationError(f"Journey {journey_id} not found")
        
        if journey.status != JourneyStatus.ACTIVE.value:
            raise StageMappingValidationError("Stage mapping must reference an active journey")

    def _validate_trigger(self, trigger_type: TriggerType, trigger_value: str) -> None:
        """Validate trigger configuration."""
        if not trigger_type:
            raise InvalidTriggerError("Trigger type is required")
            
        # Validate trigger value based on trigger type
        if trigger_type == TriggerType.LEAD_STAGE_CHANGED and not trigger_value:
            raise InvalidTriggerError("Trigger value is required for lead stage changed trigger")
        
        if trigger_type not in list(TriggerType):
            raise InvalidTriggerError(f"Invalid trigger type: {trigger_type}")

    def _validate_unique_trigger_priority(self, workspace_id: str, trigger_type: TriggerType, 
                                        trigger_value: str, priority: int, 
                                        exclude_mapping_id: str = None) -> None:
        """Validate that no other mapping has the same trigger+priority combination."""
        query = self.db.query(StageMapping).filter(
            StageMapping.workspace_id == workspace_id,
            StageMapping.trigger_type == trigger_type,
            StageMapping.priority == priority
        )
        
        if trigger_type == TriggerType.LEAD_STAGE_CHANGED:
            query = query.filter(StageMapping.trigger_value == trigger_value)
            
        if exclude_mapping_id:
            query = query.filter(StageMapping.id != exclude_mapping_id)
            
        existing_mapping = query.first()
        if existing_mapping:
            raise DuplicateStageMappingError(
                f"A stage mapping with the same trigger and priority already exists: {existing_mapping.name}"
            )

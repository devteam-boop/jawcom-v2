"""Stage Mapping Engine services."""

from typing import List, Optional
from datetime import datetime
import uuid
from sqlalchemy.orm import Session
from .schemas import (
    StageMappingSchema,
    StageMappingCreateSchema,
    StageMappingUpdateSchema,
    StageMappingStatus
)
from .validators import StageMappingValidator
from .mapping_manager import MappingManager
from .exceptions import (
    StageMappingNotFoundError,
    StageMappingValidationError,
    DuplicateStageMappingError
)
from ..models import StageMapping as StageMappingModel


class StageMappingService:
    """Service for managing stage mappings."""
    
    def __init__(self, db_session: Session):
        """Initialize stage mapping service."""
        self.db = db_session
        self.validator = StageMappingValidator(db_session)
        self.manager = MappingManager(db_session)
    
    def create_mapping(self, mapping_data: StageMappingCreateSchema) -> StageMappingSchema:
        """
        Create a new stage mapping.
        
        Args:
            mapping_data: Stage mapping creation data
            
        Returns:
            Created stage mapping schema
            
        Raises:
            StageMappingValidationError: If validation fails
            DuplicateStageMappingError: If mapping already exists
        """
        # Validate mapping data
        self.validator.validate_mapping_creation(mapping_data)
        
        # Create stage mapping model
        mapping = StageMappingModel(
            id=uuid.uuid4(),
            name=mapping_data.name,
            description=mapping_data.description,
            status=StageMappingStatus.ACTIVE.value,
            journey_id=mapping_data.journey_id,
            trigger_type=mapping_data.trigger_type.value,
            trigger_value=mapping_data.trigger_value,
            priority=mapping_data.priority,
            automation_enabled=mapping_data.automation_enabled,
            business_hours=mapping_data.business_hours.dict() if mapping_data.business_hours else None,
            retry_policy=mapping_data.retry_policy.dict() if mapping_data.retry_policy else None,
            workspace_id=mapping_data.workspace_id
        )
        
        self.db.add(mapping)
        self.db.commit()
        self.db.refresh(mapping)
        
        return self._model_to_schema(mapping)
    
    def get_mapping(self, mapping_id: str) -> StageMappingSchema:
        """
        Get stage mapping by ID.
        
        Args:
            mapping_id: Stage mapping ID
            
        Returns:
            Stage mapping schema
            
        Raises:
            StageMappingNotFoundError: If mapping not found
        """
        mapping = self.db.query(StageMappingModel).filter(StageMappingModel.id == mapping_id).first()
        if not mapping:
            raise StageMappingNotFoundError(f"Stage mapping {mapping_id} not found")
        
        return self._model_to_schema(mapping)
    
    def update_mapping(self, mapping_id: str, update_data: StageMappingUpdateSchema) -> StageMappingSchema:
        """
        Update stage mapping.
        
        Args:
            mapping_id: Stage mapping ID
            update_data: Update data
            
        Returns:
            Updated stage mapping schema
            
        Raises:
            StageMappingNotFoundError: If mapping not found
            StageMappingValidationError: If validation fails
        """
        mapping = self.db.query(StageMappingModel).filter(StageMappingModel.id == mapping_id).first()
        if not mapping:
            raise StageMappingNotFoundError(f"Stage mapping {mapping_id} not found")
        
        # Validate update data
        self.validator.validate_mapping_update(mapping_id, update_data)
        
        # Update fields if provided
        if update_data.name is not None:
            mapping.name = update_data.name
            
        if update_data.description is not None:
            mapping.description = update_data.description
            
        if update_data.status is not None:
            mapping.status = update_data.status.value
            
        if update_data.journey_id is not None:
            mapping.journey_id = update_data.journey_id
            
        if update_data.trigger_type is not None:
            mapping.trigger_type = update_data.trigger_type.value
            
        if update_data.trigger_value is not None:
            mapping.trigger_value = update_data.trigger_value
            
        if update_data.priority is not None:
            mapping.priority = update_data.priority
            
        if update_data.automation_enabled is not None:
            mapping.automation_enabled = update_data.automation_enabled
            
        if update_data.business_hours is not None:
            mapping.business_hours = update_data.business_hours.dict() if update_data.business_hours else None
            
        if update_data.retry_policy is not None:
            mapping.retry_policy = update_data.retry_policy.dict() if update_data.retry_policy else None
        
        mapping.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(mapping)
        
        return self._model_to_schema(mapping)
    
    def delete_mapping(self, mapping_id: str) -> bool:
        """
        Delete stage mapping.
        
        Args:
            mapping_id: Stage mapping ID
            
        Returns:
            True if deleted
            
        Raises:
            StageMappingNotFoundError: If mapping not found
        """
        mapping = self.db.query(StageMappingModel).filter(StageMappingModel.id == mapping_id).first()
        if not mapping:
            raise StageMappingNotFoundError(f"Stage mapping {mapping_id} not found")
        
        self.db.delete(mapping)
        self.db.commit()
        return True
    
    def list_mappings(self, workspace_id: str, status: Optional[str] = None) -> List[StageMappingSchema]:
        """
        List stage mappings for a workspace.
        
        Args:
            workspace_id: Workspace ID
            status: Optional status filter
            
        Returns:
            List of stage mapping schemas
        """
        query = self.db.query(StageMappingModel).filter(StageMappingModel.workspace_id == workspace_id)
        
        if status:
            query = query.filter(StageMappingModel.status == status)
            
        mappings = query.all()
        return [self._model_to_schema(mapping) for mapping in mappings]
    
    def enable_mapping(self, mapping_id: str) -> StageMappingSchema:
        """
        Enable a stage mapping.
        
        Args:
            mapping_id: Stage mapping ID
            
        Returns:
            Updated stage mapping schema
        """
        return self.manager.enable_mapping(mapping_id)
    
    def disable_mapping(self, mapping_id: str) -> StageMappingSchema:
        """
        Disable a stage mapping.
        
        Args:
            mapping_id: Stage mapping ID
            
        Returns:
            Updated stage mapping schema
        """
        return self.manager.disable_mapping(mapping_id)
    
    def _model_to_schema(self, mapping: StageMappingModel) -> StageMappingSchema:
        """Convert stage mapping model to schema."""
        from .schemas import BusinessHoursSchema, RetryPolicySchema
        
        business_hours = None
        if mapping.business_hours:
            business_hours = BusinessHoursSchema(**mapping.business_hours)
            
        retry_policy = None
        if mapping.retry_policy:
            retry_policy = RetryPolicySchema(**mapping.retry_policy)
        
        return StageMappingSchema(
            id=str(mapping.id),
            name=mapping.name,
            description=mapping.description,
            status=mapping.status,
            journey_id=str(mapping.journey_id),
            trigger_type=mapping.trigger_type,
            trigger_value=mapping.trigger_value,
            priority=mapping.priority,
            automation_enabled=mapping.automation_enabled,
            business_hours=business_hours,
            retry_policy=retry_policy,
            workspace_id=str(mapping.workspace_id),
            created_at=mapping.created_at,
            updated_at=mapping.updated_at
        )

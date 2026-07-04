"""Stage Mapping management utilities."""

from typing import List
from sqlalchemy.orm import Session
from .schemas import (
    StageMappingSchema,
    StageMappingStatus
)
from .exceptions import StageMappingNotFoundError
from ..models import StageMapping as StageMappingModel


class MappingManager:
    """Helper class for managing stage mappings."""

    def __init__(self, db_session: Session):
        """Initialize mapping manager."""
        self.db = db_session

    def enable_mapping(self, mapping_id: str) -> StageMappingSchema:
        """
        Enable a stage mapping.
        
        Args:
            mapping_id: Stage mapping ID
            
        Returns:
            Updated stage mapping schema
            
        Raises:
            StageMappingNotFoundError: If mapping not found
        """
        mapping = self.db.query(StageMappingModel).filter(StageMappingModel.id == mapping_id).first()
        if not mapping:
            raise StageMappingNotFoundError(f"Stage mapping {mapping_id} not found")
        
        mapping.status = StageMappingStatus.ACTIVE.value
        self.db.commit()
        self.db.refresh(mapping)
        
        return self._model_to_schema(mapping)

    def disable_mapping(self, mapping_id: str) -> StageMappingSchema:
        """
        Disable a stage mapping.
        
        Args:
            mapping_id: Stage mapping ID
            
        Returns:
            Updated stage mapping schema
            
        Raises:
            StageMappingNotFoundError: If mapping not found
        """
        mapping = self.db.query(StageMappingModel).filter(StageMappingModel.id == mapping_id).first()
        if not mapping:
            raise StageMappingNotFoundError(f"Stage mapping {mapping_id} not found")
        
        mapping.status = StageMappingStatus.INACTIVE.value
        self.db.commit()
        self.db.refresh(mapping)
        
        return self._model_to_schema(mapping)

    def get_active_mappings(self, workspace_id: str) -> List[StageMappingSchema]:
        """
        Get all active mappings for a workspace.
        
        Args:
            workspace_id: Workspace ID
            
        Returns:
            List of active stage mapping schemas
        """
        mappings = self.db.query(StageMappingModel).filter(
            StageMappingModel.workspace_id == workspace_id,
            StageMappingModel.status == StageMappingStatus.ACTIVE.value
        ).all()
        
        return [self._model_to_schema(mapping) for mapping in mappings]

    def get_mappings_by_trigger(self, workspace_id: str, trigger_type: str, 
                               trigger_value: str = None) -> List[StageMappingSchema]:
        """
        Get mappings by trigger type and value.
        
        Args:
            workspace_id: Workspace ID
            trigger_type: Trigger type
            trigger_value: Trigger value (optional)
            
        Returns:
            List of stage mapping schemas
        """
        query = self.db.query(StageMappingModel).filter(
            StageMappingModel.workspace_id == workspace_id,
            StageMappingModel.trigger_type == trigger_type
        )
        
        if trigger_value:
            query = query.filter(StageMappingModel.trigger_value == trigger_value)
            
        mappings = query.all()
        return [self._model_to_schema(mapping) for mapping in mappings]

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

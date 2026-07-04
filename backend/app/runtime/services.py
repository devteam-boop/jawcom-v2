"""Running Journey Instance Engine services."""

from typing import List, Optional
from datetime import datetime
import uuid
from sqlalchemy.orm import Session
from .schemas import (
    RunningInstanceSchema,
    RunningInstanceCreateSchema,
    RunningInstanceUpdateSchema,
    InstanceStatus
)
from .validators import RunningInstanceValidator
from .instance_manager import InstanceManager
from .exceptions import (
    RunningInstanceNotFoundError,
    RunningInstanceValidationError,
    DuplicateRunningInstanceError
)
from ..models import RunningJourneyInstance as RunningInstanceModel


class RunningInstanceService:
    """Service for managing running journey instances."""
    
    def __init__(self, db_session: Session):
        """Initialize running instance service."""
        self.db = db_session
        self.validator = RunningInstanceValidator(db_session)
        self.manager = InstanceManager(db_session)
    
    def create_instance(self, instance_data: RunningInstanceCreateSchema) -> RunningInstanceSchema:
        """
        Create a new running instance.
        
        Args:
            instance_data: Running instance creation data
            
        Returns:
            Created running instance schema
            
        Raises:
            RunningInstanceValidationError: If validation fails
            DuplicateRunningInstanceError: If instance already exists
        """
        # Validate instance data
        self.validator.validate_instance_creation(instance_data)
        
        # Create running instance model
        instance = RunningInstanceModel(
            id=uuid.uuid4(),
            lead_id=instance_data.lead_id,
            journey_id=instance_data.journey_id,
            flow_id=instance_data.flow_id,
            flow_version=instance_data.flow_version,
            status=InstanceStatus.CREATED.value,
            started_at=datetime.utcnow()
        )
        
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        
        return self._model_to_schema(instance)
    
    def get_instance(self, instance_id: str) -> RunningInstanceSchema:
        """
        Get running instance by ID.
        
        Args:
            instance_id: Running instance ID
            
        Returns:
            Running instance schema
            
        Raises:
            RunningInstanceNotFoundError: If instance not found
        """
        instance = self.db.query(RunningInstanceModel).filter(
            RunningInstanceModel.id == instance_id
        ).first()
        
        if not instance:
            raise RunningInstanceNotFoundError(f"Running instance {instance_id} not found")
        
        return self._model_to_schema(instance)
    
    def update_instance(self, instance_id: str, update_data: RunningInstanceUpdateSchema) -> RunningInstanceSchema:
        """
        Update running instance.
        
        Args:
            instance_id: Running instance ID
            update_data: Update data
            
        Returns:
            Updated running instance schema
            
        Raises:
            RunningInstanceNotFoundError: If instance not found
        """
        instance = self.db.query(RunningInstanceModel).filter(
            RunningInstanceModel.id == instance_id
        ).first()
        
        if not instance:
            raise RunningInstanceNotFoundError(f"Running instance {instance_id} not found")
        
        # Update fields if provided
        if update_data.current_node is not None:
            instance.current_node = update_data.current_node
            
        if update_data.status is not None:
            instance.status = update_data.status.value
            
        if update_data.paused_at is not None:
            instance.paused_at = update_data.paused_at
            
        if update_data.completed_at is not None:
            instance.completed_at = update_data.completed_at
            
        if update_data.last_execution is not None:
            instance.last_execution = update_data.last_execution
            
        if update_data.next_execution is not None:
            instance.next_execution = update_data.next_execution
            
        if update_data.retry_count is not None:
            instance.retry_count = update_data.retry_count
            
        if update_data.failure_reason is not None:
            instance.failure_reason = update_data.failure_reason
            
        if update_data.execution_logs is not None:
            # In a real implementation, this would serialize the logs
            # For now, we'll skip this to avoid complexity
            pass
        
        instance.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(instance)
        
        return self._model_to_schema(instance)
    
    def delete_instance(self, instance_id: str) -> bool:
        """
        Delete running instance.
        
        Args:
            instance_id: Running instance ID
            
        Returns:
            True if deleted
            
        Raises:
            RunningInstanceNotFoundError: If instance not found
        """
        instance = self.db.query(RunningInstanceModel).filter(
            RunningInstanceModel.id == instance_id
        ).first()
        
        if not instance:
            raise RunningInstanceNotFoundError(f"Running instance {instance_id} not found")
        
        self.db.delete(instance)
        self.db.commit()
        return True
    
    def list_instances(self, journey_id: Optional[str] = None, 
                      status: Optional[str] = None) -> List[RunningInstanceSchema]:
        """
        List running instances.
        
        Args:
            journey_id: Optional journey ID filter
            status: Optional status filter
            
        Returns:
            List of running instance schemas
        """
        query = self.db.query(RunningInstanceModel)
        
        if journey_id:
            query = query.filter(RunningInstanceModel.journey_id == journey_id)
            
        if status:
            query = query.filter(RunningInstanceModel.status == status)
            
        instances = query.all()
        return [self._model_to_schema(instance) for instance in instances]
    
    def pause_instance(self, instance_id: str) -> RunningInstanceSchema:
        """
        Pause a running instance.
        
        Args:
            instance_id: Running instance ID
            
        Returns:
            Updated running instance schema
        """
        return self.manager.pause_instance(instance_id)
    
    def resume_instance(self, instance_id: str) -> RunningInstanceSchema:
        """
        Resume a paused instance.
        
        Args:
            instance_id: Running instance ID
            
        Returns:
            Updated running instance schema
        """
        return self.manager.resume_instance(instance_id)
    
    def cancel_instance(self, instance_id: str) -> RunningInstanceSchema:
        """
        Cancel a running instance.
        
        Args:
            instance_id: Running instance ID
            
        Returns:
            Updated running instance schema
        """
        return self.manager.cancel_instance(instance_id)
    
    def complete_instance(self, instance_id: str) -> RunningInstanceSchema:
        """
        Complete a running instance.
        
        Args:
            instance_id: Running instance ID
            
        Returns:
            Updated running instance schema
        """
        return self.manager.complete_instance(instance_id)
    
    def _model_to_schema(self, instance: RunningInstanceModel) -> RunningInstanceSchema:
        """Convert running instance model to schema."""
        from .schemas import ExecutionLogSchema
        
        # Convert execution logs from JSON if they exist
        execution_logs = []
        if instance.execution_logs:
            # In a real implementation, this would parse the logs
            # For now, we'll create empty logs
            pass
        
        return RunningInstanceSchema(
            id=str(instance.id),
            lead_id=str(instance.lead_id),
            journey_id=str(instance.journey_id),
            flow_id=str(instance.flow_id),
            flow_version=instance.flow_version,
            current_node=instance.current_node,
            status=instance.status,
            started_at=instance.started_at,
            paused_at=instance.paused_at,
            completed_at=instance.completed_at,
            last_execution=instance.last_execution,
            next_execution=instance.next_execution,
            retry_count=instance.retry_count,
            failure_reason=instance.failure_reason,
            execution_logs=execution_logs,
            created_at=instance.created_at,
            updated_at=instance.updated_at
        )

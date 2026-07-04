"""Running Instance management utilities."""

from typing import List, Optional
from sqlalchemy.orm import Session
from .schemas import (
    RunningInstanceSchema,
    InstanceStatus
)
from .exceptions import RunningInstanceNotFoundError, InvalidInstanceStateError
from ..models import RunningJourneyInstance as RunningInstanceModel


class InstanceManager:
    """Helper class for managing running instances."""

    def __init__(self, db_session: Session):
        """Initialize instance manager."""
        self.db = db_session

    def pause_instance(self, instance_id: str) -> RunningInstanceSchema:
        """
        Pause a running instance.
        
        Args:
            instance_id: Running instance ID
            
        Returns:
            Updated running instance schema
            
        Raises:
            RunningInstanceNotFoundError: If instance not found
            InvalidInstanceStateError: If instance cannot be paused
        """
        instance = self.db.query(RunningInstanceModel).filter(
            RunningInstanceModel.id == instance_id
        ).first()
        
        if not instance:
            raise RunningInstanceNotFoundError(f"Running instance {instance_id} not found")
        
        if instance.status not in [InstanceStatus.RUNNING, InstanceStatus.WAITING]:
            raise InvalidInstanceStateError("Only running or waiting instances can be paused")
        
        from datetime import datetime
        instance.status = InstanceStatus.PAUSED.value
        instance.paused_at = datetime.utcnow()
        instance.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(instance)
        
        return self._model_to_schema(instance)

    def resume_instance(self, instance_id: str) -> RunningInstanceSchema:
        """
        Resume a paused instance.
        
        Args:
            instance_id: Running instance ID
            
        Returns:
            Updated running instance schema
            
        Raises:
            RunningInstanceNotFoundError: If instance not found
            InvalidInstanceStateError: If instance cannot be resumed
        """
        instance = self.db.query(RunningInstanceModel).filter(
            RunningInstanceModel.id == instance_id
        ).first()
        
        if not instance:
            raise RunningInstanceNotFoundError(f"Running instance {instance_id} not found")
        
        if instance.status != InstanceStatus.PAUSED.value:
            raise InvalidInstanceStateError("Only paused instances can be resumed")
        
        from datetime import datetime
        instance.status = InstanceStatus.RUNNING.value
        instance.paused_at = None
        instance.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(instance)
        
        return self._model_to_schema(instance)

    def cancel_instance(self, instance_id: str) -> RunningInstanceSchema:
        """
        Cancel a running instance.
        
        Args:
            instance_id: Running instance ID
            
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
        
        from datetime import datetime
        instance.status = InstanceStatus.CANCELLED.value
        instance.completed_at = datetime.utcnow()
        instance.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(instance)
        
        return self._model_to_schema(instance)

    def complete_instance(self, instance_id: str) -> RunningInstanceSchema:
        """
        Complete a running instance.
        
        Args:
            instance_id: Running instance ID
            
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
        
        from datetime import datetime
        instance.status = InstanceStatus.COMPLETED.value
        instance.completed_at = datetime.utcnow()
        instance.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(instance)
        
        return self._model_to_schema(instance)

    def fail_instance(self, instance_id: str, failure_reason: str) -> RunningInstanceSchema:
        """
        Fail a running instance.
        
        Args:
            instance_id: Running instance ID
            failure_reason: Reason for failure
            
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
        
        from datetime import datetime
        instance.status = InstanceStatus.FAILED.value
        instance.failure_reason = failure_reason
        instance.completed_at = datetime.utcnow()
        instance.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(instance)
        
        return self._model_to_schema(instance)

    def get_active_instances(self, journey_id: str) -> List[RunningInstanceSchema]:
        """
        Get all active instances for a journey.
        
        Args:
            journey_id: Journey ID
            
        Returns:
            List of active running instance schemas
        """
        instances = self.db.query(RunningInstanceModel).filter(
            RunningInstanceModel.journey_id == journey_id,
            RunningInstanceModel.status.in_([
                InstanceStatus.CREATED.value,
                InstanceStatus.RUNNING.value,
                InstanceStatus.WAITING.value,
                InstanceStatus.PAUSED.value
            ])
        ).all()
        
        return [self._model_to_schema(instance) for instance in instances]

    def _model_to_schema(self, instance: RunningInstanceModel) -> RunningInstanceSchema:
        """Convert running instance model to schema."""
        from .schemas import ExecutionLogSchema
        from datetime import datetime
        
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

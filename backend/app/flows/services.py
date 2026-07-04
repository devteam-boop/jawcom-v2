"""Flow Definition Engine services."""

from typing import List, Optional
from datetime import datetime
import uuid
from sqlalchemy.orm import Session
from .schemas import (
    FlowDefinitionSchema,
    FlowVersionSchema,
    FlowCreateSchema,
    FlowUpdateSchema,
    FlowPublishSchema,
    FlowStatus,
    NodeSchema,
    EdgeSchema
)
from .validators import FlowValidator
from .flow_builder import FlowBuilder
from .exceptions import (
    FlowValidationError,
    FlowPublishError,
    FlowVersionError
)
from ..models import FlowDefinition, Journey
from ..templates.services import TemplateService


class FlowService:
    """Service for managing flow definitions."""
    
    def __init__(self, db_session: Session, template_service: TemplateService):
        """Initialize flow service."""
        self.db = db_session
        self.template_service = template_service
        self.validator = FlowValidator(template_service)
    
    def create_flow(self, flow_data: FlowCreateSchema) -> FlowDefinitionSchema:
        """
        Create a new flow definition.
        
        Args:
            flow_data: Flow creation data
            
        Returns:
            Created flow definition schema
        """
        # Create flow definition model
        flow = FlowDefinition(
            id=uuid.uuid4(),
            name=flow_data.name,
            description=flow_data.description,
            definition="",  # Empty initial definition
            status=FlowStatus.DRAFT.value,
            version=1,
            is_active=True,
            workspace_id=flow_data.workspace_id
        )
        
        self.db.add(flow)
        self.db.commit()
        self.db.refresh(flow)
        
        return self._model_to_schema(flow)
    
    def get_flow(self, flow_id: str) -> FlowDefinitionSchema:
        """
        Get flow definition by ID.
        
        Args:
            flow_id: Flow ID
            
        Returns:
            Flow definition schema
        """
        flow = self.db.query(FlowDefinition).filter(FlowDefinition.id == flow_id).first()
        if not flow:
            raise FlowValidationError(f"Flow {flow_id} not found")
        
        return self._model_to_schema(flow)
    
    def update_flow(self, flow_id: str, update_data: FlowUpdateSchema) -> FlowDefinitionSchema:
        """
        Update flow definition.
        
        Args:
            flow_id: Flow ID
            update_data: Update data
            
        Returns:
            Updated flow definition schema
            
        Raises:
            FlowValidationError: If validation fails
        """
        flow = self.db.query(FlowDefinition).filter(FlowDefinition.id == flow_id).first()
        if not flow:
            raise FlowValidationError(f"Flow {flow_id} not found")
        
        # Update fields if provided
        if update_data.name is not None:
            flow.name = update_data.name
            
        if update_data.description is not None:
            flow.description = update_data.description
            
        # Validate flow structure if nodes/edges are updated
        if update_data.nodes is not None or update_data.edges is not None:
            # Create temporary flow for validation
            temp_flow = FlowDefinitionSchema(
                id=str(flow.id),
                name=flow.name,
                description=flow.description,
                nodes=update_data.nodes or [],
                edges=update_data.edges or [],
                status=flow.status,
                version=flow.version,
                is_active=flow.is_active,
                created_at=flow.created_at,
                updated_at=flow.updated_at,
                workspace_id=str(flow.workspace_id)
            )
            
            self.validator.validate_flow_structure(temp_flow)
            
            # Update flow definition JSON
            flow.definition = self._serialize_flow_definition(
                update_data.nodes or [],
                update_data.edges or []
            )
        
        flow.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(flow)
        
        return self._model_to_schema(flow)
    
    def delete_flow(self, flow_id: str) -> bool:
        """
        Delete flow definition.
        
        Args:
            flow_id: Flow ID
            
        Returns:
            True if deleted
            
        Raises:
            FlowValidationError: If flow not found
            FlowValidationError: If flow is in use
        """
        flow = self.db.query(FlowDefinition).filter(FlowDefinition.id == flow_id).first()
        if not flow:
            raise FlowValidationError(f"Flow {flow_id} not found")
        
        # Check if flow is in use by journeys
        journey_count = self.db.query(Journey).filter(Journey.flow_definition_id == flow_id).count()
        if journey_count > 0:
            raise FlowValidationError("Flow is currently in use by journeys and cannot be deleted")
        
        self.db.delete(flow)
        self.db.commit()
        return True
    
    def publish_flow(self, publish_data: FlowPublishSchema) -> FlowDefinitionSchema:
        """
        Publish a flow version.
        
        Args:
            publish_data: Publish data
            
        Returns:
            Published flow definition schema
            
        Raises:
            FlowPublishError: If publishing fails
        """
        flow = self.db.query(FlowDefinition).filter(
            FlowDefinition.id == publish_data.flow_id
        ).first()
        
        if not flow:
            raise FlowPublishError(f"Flow {publish_data.flow_id} not found")
        
        # Check if there's already a published version
        published_flow = self.db.query(FlowDefinition).filter(
            FlowDefinition.journey_id == flow.journey_id,
            FlowDefinition.status == FlowStatus.PUBLISHED.value
        ).first()
        
        if published_flow and published_flow.id != flow.id:
            # Archive the existing published version
            published_flow.status = FlowStatus.ARCHIVED.value
            published_flow.updated_at = datetime.utcnow()
        
        # Publish the current flow
        flow.status = FlowStatus.PUBLISHED.value
        flow.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(flow)
        
        return self._model_to_schema(flow)
    
    def list_flows(self, workspace_id: str) -> List[FlowDefinitionSchema]:
        """
        List flows for a workspace.
        
        Args:
            workspace_id: Workspace ID
            
        Returns:
            List of flow definition schemas
        """
        flows = self.db.query(FlowDefinition).filter(
            FlowDefinition.workspace_id == workspace_id
        ).all()
        
        return [self._model_to_schema(flow) for flow in flows]
    
    def get_flow_versions(self, flow_id: str) -> List[FlowVersionSchema]:
        """
        Get all versions of a flow.
        
        Args:
            flow_id: Flow ID
            
        Returns:
            List of flow version schemas
        """
        # In a real implementation, this would query version history
        # For now, returning just the current version
        flow = self.db.query(FlowDefinition).filter(
            FlowDefinition.id == flow_id
        ).first()
        
        if not flow:
            raise FlowValidationError(f"Flow {flow_id} not found")
        
        return [
            FlowVersionSchema(
                id=str(flow.id),
                flow_id=flow_id,
                version=flow.version,
                is_active=flow.is_active,
                status=flow.status,
                created_at=flow.created_at
            )
        ]
    
    def _model_to_schema(self, flow: FlowDefinition) -> FlowDefinitionSchema:
        """Convert flow model to schema."""
        # Parse the flow definition JSON
        nodes, edges = self._deserialize_flow_definition(flow.definition)
        
        return FlowDefinitionSchema(
            id=str(flow.id),
            name=flow.name,
            description=flow.description,
            nodes=nodes,
            edges=edges,
            status=flow.status,
            version=flow.version,
            is_active=flow.is_active,
            created_at=flow.created_at,
            updated_at=flow.updated_at,
            workspace_id=str(flow.workspace_id)
        )
    
    def _serialize_flow_definition(self, nodes: List[NodeSchema], 
                                 edges: List[EdgeSchema]) -> str:
        """Serialize flow definition to JSON string."""
        import json
        return json.dumps({
            "nodes": [node.dict() for node in nodes],
            "edges": [edge.dict() for edge in edges]
        })
    
    def _deserialize_flow_definition(self, definition: str) -> tuple:
        """Deserialize flow definition from JSON string."""
        import json
        from .schemas import NodeSchema, EdgeSchema
        
        if not definition:
            return [], []
            
        try:
            data = json.loads(definition)
            nodes = [NodeSchema(**node_data) for node_data in data.get("nodes", [])]
            edges = [EdgeSchema(**edge_data) for edge_data in data.get("edges", [])]
            return nodes, edges
        except Exception:
            return [], []

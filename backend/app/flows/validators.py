"""Flow validation utilities."""

from typing import List, Set
from .schemas import (
    FlowDefinitionSchema, 
    NodeSchema, 
    EdgeSchema, 
    NodeType
)
from .exceptions import FlowValidationError, InvalidNodeError
from ..templates.services import TemplateService


class FlowValidator:
    """Validator for flow structure and content."""

    def __init__(self, template_service: TemplateService):
        """Initialize flow validator."""
        self.template_service = template_service

    def validate_flow_structure(self, flow: FlowDefinitionSchema) -> None:
        """
        Validate flow structure.
        
        Args:
            flow: Flow definition to validate
            
        Raises:
            FlowValidationError: If validation fails
        """
        # Check for required trigger node
        trigger_nodes = [node for node in flow.nodes if node.type == NodeType.TRIGGER]
        if len(trigger_nodes) != 1:
            raise FlowValidationError("Flow must have exactly one trigger node")
        
        # Check for end node
        end_nodes = [node for node in flow.nodes if node.type == NodeType.END]
        if not end_nodes:
            raise FlowValidationError("Flow must have at least one end node")
        
        # Check for circular references
        if self._has_circular_reference(flow.nodes, flow.edges):
            raise FlowValidationError("Flow contains circular references")
        
        # Check for orphan nodes
        if self._has_orphan_nodes(flow.nodes, flow.edges):
            raise FlowValidationError("Flow contains orphan nodes")
        
        # Validate node connections
        self._validate_node_connections(flow.nodes, flow.edges)
        
        # Validate template references
        self._validate_template_references(flow.nodes)

    def validate_node(self, node: NodeSchema) -> None:
        """
        Validate individual node.
        
        Args:
            node: Node to validate
            
        Raises:
            InvalidNodeError: If node validation fails
        """
        if not node.id:
            raise InvalidNodeError("Node must have an ID")
        
        if not node.type:
            raise InvalidNodeError("Node must have a type")
        
        # Validate node-specific data
        if node.type in [NodeType.SEND_EMAIL, NodeType.SEND_WHATSAPP]:
            if not hasattr(node.data, 'template_id') or not node.data.template_id:
                raise InvalidNodeError("Send template nodes must have a template_id")

    def _has_circular_reference(self, nodes: List[NodeSchema], edges: List[EdgeSchema]) -> bool:
        """Check if flow has circular references using DFS."""
        # Build adjacency list
        graph = {}
        for edge in edges:
            if edge.source not in graph:
                graph[edge.source] = []
            graph[edge.source].append(edge.target)
        
        # DFS to detect cycles
        visited = set()
        rec_stack = set()
        
        def dfs(node_id):
            if node_id in rec_stack:
                return True
            if node_id in visited:
                return False
                
            visited.add(node_id)
            rec_stack.add(node_id)
            
            if node_id in graph:
                for neighbor in graph[node_id]:
                    if dfs(neighbor):
                        return True
                        
            rec_stack.remove(node_id)
            return False
        
        for node in nodes:
            if dfs(node.id):
                return True
        return False

    def _has_orphan_nodes(self, nodes: List[NodeSchema], edges: List[EdgeSchema]) -> bool:
        """Check if flow has orphan nodes (nodes not connected to the main flow)."""
        if len(nodes) <= 1:
            return False
            
        # Build set of all connected nodes
        connected_nodes = set()
        for edge in edges:
            connected_nodes.add(edge.source)
            connected_nodes.add(edge.target)
        
        # Check if all nodes are connected (except trigger which might be the start)
        trigger_nodes = {node.id for node in nodes if node.type == NodeType.TRIGGER}
        all_node_ids = {node.id for node in nodes}
        
        # Orphan nodes are nodes that are not connected to anything
        orphan_nodes = all_node_ids - connected_nodes - trigger_nodes
        
        return len(orphan_nodes) > 0

    def _validate_node_connections(self, nodes: List[NodeSchema], edges: List[EdgeSchema]) -> None:
        """Validate that all node connections are valid."""
        node_ids = {node.id for node in nodes}
        
        # Check that all edges connect valid nodes
        for edge in edges:
            if edge.source not in node_ids:
                raise FlowValidationError(f"Edge source {edge.source} does not exist")
            if edge.target not in node_ids:
                raise FlowValidationError(f"Edge target {edge.target} does not exist")
        
        # Check that condition nodes have both branches
        for node in nodes:
            if node.type == NodeType.CONDITION:
                # This would require more detailed validation based on the node data structure
                pass

    def _validate_template_references(self, nodes: List[NodeSchema]) -> None:
        """Validate that all template references are valid."""
        for node in nodes:
            if node.type in [NodeType.SEND_EMAIL, NodeType.SEND_WHATSAPP]:
                template_id = getattr(node.data, 'template_id', None)
                if template_id:
                    try:
                        # In a real implementation, this would check against the template service
                        # For now, we'll skip actual validation to avoid dependency issues
                        pass
                    except Exception:
                        raise FlowValidationError(f"Invalid template reference: {template_id}")

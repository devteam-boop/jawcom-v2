"""Flow builder utilities."""

from typing import List, Dict, Any
from uuid import uuid4
from .schemas import (
    NodeSchema, 
    EdgeSchema, 
    NodeType,
    TriggerNodeData,
    DelayNodeData,
    ConditionNodeData,
    SendTemplateNodeData,
    NotificationNodeData,
    WaitNodeData
)


class FlowBuilder:
    """Helper class for building flows programmatically."""

    def __init__(self):
        """Initialize flow builder."""
        self.nodes: List[NodeSchema] = []
        self.edges: List[EdgeSchema] = []
        self.node_counter = 0

    def add_trigger_node(self, event_type: str, criteria: Dict[str, Any] = None, 
                        position: Dict[str, int] = None) -> str:
        """Add a trigger node to the flow."""
        node_id = f"node_{self.node_counter}"
        self.node_counter += 1
        
        node = NodeSchema(
            id=node_id,
            type=NodeType.TRIGGER,
            data=TriggerNodeData(
                event_type=event_type,
                criteria=criteria or {}
            ),
            position=position or {"x": 0, "y": 0},
            label="Trigger"
        )
        
        self.nodes.append(node)
        return node_id

    def add_delay_node(self, duration: int, unit: str = "seconds",
                      position: Dict[str, int] = None) -> str:
        """Add a delay node to the flow."""
        node_id = f"node_{self.node_counter}"
        self.node_counter += 1
        
        node = NodeSchema(
            id=node_id,
            type=NodeType.DELAY,
            data=DelayNodeData(
                duration=duration,
                unit=unit
            ),
            position=position or {"x": 0, "y": 0},
            label=f"Delay {duration} {unit}"
        )
        
        self.nodes.append(node)
        return node_id

    def add_condition_node(self, condition_type: str, parameters: Dict[str, Any],
                          true_branch: str, false_branch: str,
                          position: Dict[str, int] = None) -> str:
        """Add a condition node to the flow."""
        node_id = f"node_{self.node_counter}"
        self.node_counter += 1
        
        node = NodeSchema(
            id=node_id,
            type=NodeType.CONDITION,
            data=ConditionNodeData(
                condition_type=condition_type,
                parameters=parameters,
                true_branch=true_branch,
                false_branch=false_branch
            ),
            position=position or {"x": 0, "y": 0},
            label=f"Condition: {condition_type}"
        )
        
        self.nodes.append(node)
        return node_id

    def add_send_email_node(self, template_id: str, recipient_variable: str = "lead",
                           position: Dict[str, int] = None) -> str:
        """Add a send email node to the flow."""
        node_id = f"node_{self.node_counter}"
        self.node_counter += 1
        
        node = NodeSchema(
            id=node_id,
            type=NodeType.SEND_EMAIL,
            data=SendTemplateNodeData(
                template_id=template_id,
                recipient_variable=recipient_variable
            ),
            position=position or {"x": 0, "y": 0},
            label=f"Send Email: {template_id}"
        )
        
        self.nodes.append(node)
        return node_id

    def add_send_whatsapp_node(self, template_id: str, recipient_variable: str = "lead",
                              position: Dict[str, int] = None) -> str:
        """Add a send WhatsApp node to the flow."""
        node_id = f"node_{self.node_counter}"
        self.node_counter += 1
        
        node = NodeSchema(
            id=node_id,
            type=NodeType.SEND_WHATSAPP,
            data=SendTemplateNodeData(
                template_id=template_id,
                recipient_variable=recipient_variable
            ),
            position=position or {"x": 0, "y": 0},
            label=f"Send WhatsApp: {template_id}"
        )
        
        self.nodes.append(node)
        return node_id

    def add_notification_node(self, message: str, recipients: List[str] = None,
                             position: Dict[str, int] = None) -> str:
        """Add a notification node to the flow."""
        node_id = f"node_{self.node_counter}"
        self.node_counter += 1
        
        node = NodeSchema(
            id=node_id,
            type=NodeType.NOTIFICATION,
            data=NotificationNodeData(
                message=message,
                recipients=recipients or []
            ),
            position=position or {"x": 0, "y": 0},
            label="Notification"
        )
        
        self.nodes.append(node)
        return node_id

    def add_wait_node(self, wait_type: str, parameters: Dict[str, Any],
                     position: Dict[str, int] = None) -> str:
        """Add a wait node to the flow."""
        node_id = f"node_{self.node_counter}"
        self.node_counter += 1
        
        node = NodeSchema(
            id=node_id,
            type=NodeType.WAIT,
            data=WaitNodeData(
                wait_type=wait_type,
                parameters=parameters
            ),
            position=position or {"x": 0, "y": 0},
            label=f"Wait: {wait_type}"
        )
        
        self.nodes.append(node)
        return node_id

    def add_end_node(self, position: Dict[str, int] = None) -> str:
        """Add an end node to the flow."""
        node_id = f"node_{self.node_counter}"
        self.node_counter += 1
        
        node = NodeSchema(
            id=node_id,
            type=NodeType.END,
            data={},
            position=position or {"x": 0, "y": 0},
            label="End"
        )
        
        self.nodes.append(node)
        return node_id

    def connect_nodes(self, source_id: str, target_id: str,
                     source_handle: str = None, target_handle: str = None) -> str:
        """Connect two nodes with an edge."""
        edge_id = f"edge_{uuid4().hex[:8]}"
        
        edge = EdgeSchema(
            id=edge_id,
            source=source_id,
            target=target_id,
            source_handle=source_handle,
            target_handle=target_handle
        )
        
        self.edges.append(edge)
        return edge_id

    def build(self) -> Dict[str, Any]:
        """Build the flow definition."""
        return {
            "nodes": self.nodes,
            "edges": self.edges
        }

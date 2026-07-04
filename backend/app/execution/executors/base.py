"""Base executor contract for the node execution framework.

Every concrete node executor must inherit from :class:`BaseNodeExecutor`
and implement ``execute``. The ExecutionEngine only knows this interface;
it never contains business logic for individual node types.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class ExecutionResult:
    """Result returned by every node executor.

    Attributes:
        success: True if the node completed successfully.
        next_node_id: ID of the next node to visit, or None if this is a terminal branch.
        updated_context: Optionally mutated execution context.
        error: Human-readable error message when ``success`` is False.
        status: Normalized status string: "success", "failed", or "skipped".
        output: Arbitrary output payload to persist in the execution log.
    """

    success: bool
    next_node_id: Optional[str] = None
    updated_context: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    status: str = "success"
    output: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        if self.status is None:
            self.status = "success" if self.success else "failed"


@dataclass
class ExecutionContext:
    """Execution context passed to each executor.

    This object is intentionally plain and JSON-serializable-friendly so
    that context snapshots can be stored in running instance data.
    """

    lead_id: int
    instance_id: str
    flow_definition_id: str
    node_id: str
    node_type: str
    node_data: Dict[str, Any]
    context: Dict[str, Any]
    started_at: Optional[datetime] = None


class BaseNodeExecutor(ABC):
    """Common interface for all node executors.

    A concrete executor is responsible ONLY for the behaviour of a single
    node type. Graph traversal, logging, and instance state management are
    owned by the ExecutionEngine.
    """

    @property
    @abstractmethod
    def node_type(self) -> str:
        """The flow node type this executor handles, e.g. ``send_whatsapp``."""
        ...

    @abstractmethod
    async def execute(
        self,
        node: Dict[str, Any],
        running_instance: Any,
        lead_id: int,
        context: Dict[str, Any],
    ) -> ExecutionResult:
        """Execute the node.

        Args:
            node: The flow node definition (contains ``id``, ``type``, ``data``).
            running_instance: The RunningJourneyInstance model/row the engine is updating.
            lead_id: The lead identifier.
            context: Mutable execution context shared across nodes.

        Returns:
            ExecutionResult with success, next node, context updates and optional error.
        """
        ...

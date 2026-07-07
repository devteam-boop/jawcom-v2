"""Base executor contract for the node execution framework.

Every concrete node executor must inherit from :class:`BaseNodeExecutor`
and implement ``execute``. The ExecutionEngine only knows this interface;
it never contains business logic for individual node types.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
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
    """Rich execution context passed to every node executor.

    Contains resolved lead/company data, journey metadata, execution
    timestamps, a ``VariableResolverService`` for resolving
    ``{{variable}}`` placeholders inside node configuration, and a
    ``TemplateService`` for resolving ``node.config.template_id`` into
    actual template content (executors never query the database directly).
    """

    lead_id: int
    lead: Dict[str, Any]
    company: Optional[Dict[str, Any]] = None
    journey_name: str = ""
    instance_id: str = ""
    flow_definition_id: str = ""
    execution_time: Optional[datetime] = None
    node_outputs: Optional[Dict[str, Any]] = field(default_factory=dict)
    resolver: Any = None
    renderer: Any = None
    template_service: Any = None
    context: Optional[Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Flatten context into a variable-resolution dict."""
        now = self.execution_time or datetime.utcnow()
        return {
            "lead": self.lead or {},
            "company": self.company or {},
            "journey": {"name": self.journey_name},
            "execution": {
                "id": self.instance_id,
                "flow_definition_id": self.flow_definition_id,
            },
            "today": now.strftime("%Y-%m-%d"),
            "now": now.isoformat(),
            "node_outputs": self.node_outputs or {},
        }


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
        exec_ctx: Optional[ExecutionContext] = None,
    ) -> ExecutionResult:
        """Execute the node.

        Args:
            node: The flow node definition (contains ``id``, ``type``, ``data``).
            running_instance: The RunningJourneyInstance model/row the engine is updating.
            lead_id: The lead identifier.
            context: Mutable execution context shared across nodes.
            exec_ctx: Rich ExecutionContext with resolved lead/company data,
                      variable resolver, and execution metadata.

        Returns:
            ExecutionResult with success, next node, context updates and optional error.
        """
        ...

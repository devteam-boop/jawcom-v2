"""Execution Engine — orchestrates journey flows triggered by JAWIS business events.

Execution flow (end-to-end):

    Webhook / Test Call
           │
           ▼
     Stage Key
           │
           ▼
     Find Stage Mapping  ─── stage_mappings(stage_key)
           │
           ▼
     Journey              ─── journeys(id = stage_mapping.journey_id)
           │
           ▼
     Flow Definition      ─── flow_definitions(id = journey.flow_definition_id)
           │
           ▼
     Running Instance     ─── running_journey_instances (created)
           │
           ▼
     Execution Logs       ─── flow_execution_logs (one per node traversed)

The source of truth for the trigger stage is **stage_mappings**.
``journey.trigger_value`` is NOT used as a business source.
"""

import logging
from typing import Any, Dict, Optional
from uuid import UUID

from app.database.session import async_session_maker
from app.events.event_types import (
    LeadCreatedEvent,
    LeadStageChangedEvent,
)
from app.models.flow_definition import FlowDefinition, FlowDefinitionStatus
from app.models.journey import JourneyStatus
from app.repositories.stage_mapping_repository import StageMappingRepository
from app.services.journey_service import JourneyService
from app.services.running_instance_service import RunningInstanceService
from app.services.flow_execution_log_service import FlowExecutionLogService
from app.runtime.schemas import RunningInstanceCreateSchema
from app.flow_definitions.schemas import FlowExecutionLogCreateSchema

logger = logging.getLogger(__name__)


class ExecutionEngine:
    """Orchestrates journey execution when a JAWIS business event arrives.

    Resolution chain:

        stage_key
            ↓
        stage_mapping  (via StageMappingRepository.get_by_stage_key)
            ↓
        journey_id
            ↓
        journey        (must be active)
            ↓
        flow_definition (published, via journey.flow_definition_id)
            ↓
        running_instance + execution_logs

    Public entry points:
        handle_lead_created(event)
        handle_lead_stage_changed(event)
        test_execution(journey_id, lead_id, stage_key)  — direct test without webhook
    """

    def __init__(self, session_factory=None):
        self._session_factory = session_factory or async_session_maker

    # ------------------------------------------------------------------
    # Public entry points – one per event type + test
    # ------------------------------------------------------------------

    async def test_execution(self, journey_id: str, lead_id: int, stage_key: str) -> bool:
        """Execute a journey directly for testing, without a webhook event.

        Args:
            journey_id: The journey to execute.
            lead_id:    The lead to create an instance for.
            stage_key:  The stage key to match against stage_mappings.

        Resolution:
            stage_key → stage_mapping → journey_id → flow_definition → instance + logs
        """
        logger.info("ExecutionEngine.test_execution – journey=%s lead=%d stage=%s", journey_id, lead_id, stage_key)
        return await self._execute_for_stage(str(lead_id), stage_key)

    # ------------------------------------------------------------------
    # Public entry points – one per event type
    # ------------------------------------------------------------------

    async def handle_lead_created(self, event: LeadCreatedEvent) -> bool:
        """Handle a lead.created event."""
        stage_key = event.stage_key
        lead_id = event.lead_id
        logger.info("ExecutionEngine handling lead.created – lead=%s stage=%s", lead_id, stage_key)
        return await self._execute_for_stage(lead_id, stage_key)

    async def handle_lead_stage_changed(self, event: LeadStageChangedEvent) -> bool:
        """Handle a lead.stage_changed event."""
        to_stage_key = event.to_stage_key
        lead_id = event.lead_id
        logger.info(
            "ExecutionEngine handling lead.stage_changed – lead=%s to_stage=%s",
            lead_id, to_stage_key,
        )
        return await self._execute_for_stage(lead_id, to_stage_key)

    # ------------------------------------------------------------------
    # Internal orchestration
    # ------------------------------------------------------------------

    async def _execute_for_stage(self, lead_id: str, stage_key: str) -> bool:
        """Core orchestration shared by all event types."""
        async with self._session_factory() as session:
            try:
                repo = StageMappingRepository(session)
                journey_service = JourneyService(session)
                instance_service = RunningInstanceService(session)
                log_service = FlowExecutionLogService(session)

                # 1. Find matching stage mappings
                mappings = await repo.get_by_stage_key(stage_key)
                if not mappings:
                    logger.info("No stage mappings found for stage_key=%s", stage_key)
                    return True

                any_triggered = False

                for mapping in mappings:
                    # 2. Load the linked Journey (must be active)
                    try:
                        journey = await journey_service.get(mapping.journey_id)
                    except ValueError:
                        logger.warning("Journey %s not found, skipping mapping %s", mapping.journey_id, mapping.id)
                        continue

                    if journey.status != JourneyStatus.ACTIVE:
                        logger.info("Journey %s is %s, skipping", journey.id, journey.status)
                        continue

                    # 3. Create running journey instance
                    instance_schema = RunningInstanceCreateSchema(
                        lead_id=int(lead_id),
                        journey_id=str(mapping.journey_id),
                        current_stage_mapping_id=str(mapping.id),
                        data={"trigger_stage_key": stage_key},
                    )
                    instance = await instance_service.create(instance_schema)

                    # 4. Load the published FlowDefinition via the explicit FK
                    flow_def = await self._load_flow_definition(journey)

                    if flow_def is None:
                        logger.error(
                            "Journey %s has no flow_definition_id — stopping execution for instance %s",
                            journey.id, instance.id,
                        )
                        continue

                    # 5. Determine the first node to execute (trigger node)
                    first_node_id = self._resolve_first_node(flow_def.definition)

                    # 6. Create the first flow execution log
                    log_schema = FlowExecutionLogCreateSchema(
                        flow_definition_id=str(flow_def.id),
                        running_instance_id=instance.id,
                        lead_id=int(lead_id),
                        node_id=first_node_id,
                        status="success",
                        input={"event": "lead.stage_changed", "stage_key": stage_key, "lead_id": lead_id},
                        output={},
                    )
                    await log_service.create(log_schema)

                    # 7. Traverse the rest of the flow nodes (post-trigger)
                    await self._traverse_flow(
                        definition=flow_def.definition,
                        instance_id=instance.id,
                        flow_def_id=str(flow_def.id),
                        lead_id=int(lead_id),
                        start_node_id=first_node_id,
                        session=session,
                    )

                    logger.info(
                        "Journey %s activated for lead %s – instance=%s flow=%s first_node=%s",
                        journey.id, lead_id, instance.id, flow_def.id, first_node_id,
                    )
                    any_triggered = True

                return any_triggered

            except Exception as exc:
                logger.error("ExecutionEngine error for lead=%s stage=%s: %s", lead_id, stage_key, exc)
                return False

    # ------------------------------------------------------------------
    # Flow traversal
    # ------------------------------------------------------------------

    async def _traverse_flow(
        self,
        definition: Dict[str, Any],
        instance_id: str,
        flow_def_id: str,
        lead_id: int,
        start_node_id: str,
        session,
    ) -> None:
        """Walk through the flow graph starting from edges out of *start_node_id*.

        Each visited node (except the start node itself, which was already
        logged as the trigger) gets a ``FlowExecutionLog``.  When an ``end``
        node is reached, the running instance is marked completed and traversal
        stops.
        """
        nodes = definition.get("nodes") or []
        edges = definition.get("edges") or []

        node_map: Dict[str, Any] = {n["id"]: n for n in nodes}

        # build adjacency: node_id -> list of next node IDs
        adjacency: Dict[str, list] = {}
        for edge in edges:
            src = edge.get("source")
            tgt = edge.get("target")
            if src and tgt:
                adjacency.setdefault(src, []).append(tgt)

        log_service = FlowExecutionLogService(session)
        instance_service = RunningInstanceService(session)

        queue = list(adjacency.get(start_node_id, []))
        visited = {start_node_id}

        while queue:
            node_id = queue.pop(0)
            if node_id in visited:
                continue
            visited.add(node_id)

            node = node_map.get(node_id)
            if not node:
                continue

            node_type = node.get("type", "")

            if node_type == "end":
                await instance_service.complete(UUID(instance_id))
                log_schema = FlowExecutionLogCreateSchema(
                    flow_definition_id=flow_def_id,
                    running_instance_id=instance_id,
                    lead_id=lead_id,
                    node_id=node_id,
                    status="success",
                    input={},
                    output={},
                )
                await log_service.create(log_schema)
                return

            await log_service.create(
                FlowExecutionLogCreateSchema(
                    flow_definition_id=flow_def_id,
                    running_instance_id=instance_id,
                    lead_id=lead_id,
                    node_id=node_id,
                    status="success",
                    input={},
                    output={},
                )
            )

            next_nodes = adjacency.get(node_id, [])
            queue.extend(next_nodes)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _load_flow_definition(
        self, journey: Any,
    ) -> Optional[FlowDefinition]:
        """Resolve the published FlowDefinition via the explicit FK.

        Returns None (and logs an error) when ``journey.flow_definition_id``
        is NULL — execution is aborted for that journey.
        """
        if not journey.flow_definition_id:
            logger.error(
                "Journey %s has NULL flow_definition_id — cannot resolve flow definition",
                journey.id,
            )
            return None

        async with self._session_factory() as session:
            from sqlalchemy import select
            stmt = select(FlowDefinition).where(
                FlowDefinition.id == journey.flow_definition_id,
                FlowDefinition.status == FlowDefinitionStatus.PUBLISHED.value,
            )
            result = await session.execute(stmt)
            flow_def = result.scalar_one_or_none()

        if flow_def is None:
            logger.error(
                "Flow definition %s not found or not published for journey %s",
                journey.flow_definition_id, journey.id,
            )

        return flow_def

    @staticmethod
    def _resolve_first_node(definition: Dict[str, Any]) -> str:
        """Return the ID of the first node to execute.

        Prefers a node typed ``trigger``; falls back to the first node in the
        ``nodes`` array, or ``"trigger"`` when the definition is empty.
        """
        nodes = definition.get("nodes") if definition else []
        if not nodes:
            return "trigger"

        for node in nodes:
            if node.get("type") == "trigger":
                return node.get("id", "trigger")

        return nodes[0].get("id", "trigger")

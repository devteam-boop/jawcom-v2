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
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.database.session import async_session_maker
from app.events.event_types import (
    LeadCreatedEvent,
    LeadStageChangedEvent,
)
from app.execution.executors import ExecutorFactory
from app.execution.executors.base import ExecutionContext
from app.execution.providers import LeadProvider, LeadProviderFactory
from app.services.template_renderer_service import TemplateRendererService
from app.templates.services import TemplateService
from app.models.flow_definition import FlowDefinition, FlowDefinitionStatus
from app.models.journey import JourneyStatus
from app.repositories.stage_mapping_repository import StageMappingRepository
from app.services.journey_service import JourneyService
from app.services.running_instance_service import RunningInstanceService
from app.services.flow_execution_log_service import FlowExecutionLogService
from app.services.variable_resolver_service import VariableResolverService
from app.services.communication_event_service import CommunicationEventService
from app.runtime.schemas import RunningInstanceCreateSchema, RunningInstanceUpdateSchema
from app.flow_definitions.schemas import FlowExecutionLogCreateSchema
from app.communication_events.schemas import CommunicationEventCreateSchema
from app.models.communication_event import CommunicationEventType, CommunicationEventChannel

logger = logging.getLogger(__name__)

# Node type -> communication event mapping. Only node types with a
# required Sprint 1 event are listed; anything absent here is silently
# skipped by _record_communication_event (e.g. delay/end/approval nodes).
_NODE_TYPE_TO_EVENT_TYPE = {
    "trigger": CommunicationEventType.TRIGGER_EXECUTED.value,
    "condition": CommunicationEventType.CONDITION_EVALUATED.value,
    "wait": CommunicationEventType.WAIT_STARTED.value,
    "send_whatsapp": CommunicationEventType.WHATSAPP_SENT.value,
    "send_email": CommunicationEventType.EMAIL_SENT.value,
    "create_note": CommunicationEventType.NOTE_ADDED.value,
    "manual_task": CommunicationEventType.TASK_CREATED.value,
    "notification": CommunicationEventType.NOTIFICATION_SENT.value,
}

_NODE_TYPE_TO_CHANNEL = {
    "send_whatsapp": CommunicationEventChannel.WHATSAPP.value,
    "send_email": CommunicationEventChannel.EMAIL.value,
}


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
    # Public entry points
    # ------------------------------------------------------------------

    async def test_execution(self, journey_id: str, lead_id: int, stage_key: str) -> bool:
        """Execute a journey directly for testing, without a webhook event."""
        logger.info("ExecutionEngine.test_execution – journey=%s lead=%d stage=%s", journey_id, lead_id, stage_key)
        return await self._execute_for_stage(str(lead_id), stage_key)

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
        """Core orchestration shared by all event types.

        Flow:
            1. Load stage mappings for the given stage_key
            2. For each active journey, create a running instance
            3. Load the published flow definition
            4. Dispatch the trigger node through its executor
            5. Traverse the remaining graph, dispatching every node
               through its registered executor
        """
        async with self._session_factory() as session:
            try:
                repo = StageMappingRepository(session)
                journey_service = JourneyService(session)
                instance_service = RunningInstanceService(session)
                log_service = FlowExecutionLogService(session)
                event_service = CommunicationEventService(session)
                lead_provider: LeadProvider = LeadProviderFactory.get_provider()

                # 1. Find matching stage mappings
                mappings = await repo.get_by_stage_key(stage_key)
                if not mappings:
                    logger.info("No stage mappings found for stage_key=%s", stage_key)
                    return True

                any_triggered = False

                # Resolve lead context once (shared across journeys for this lead)
                lead_context = await lead_provider.get_lead_context(int(lead_id))
                execution_time = datetime.utcnow()

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

                    await self._record_communication_event(
                        event_service=event_service,
                        running_instance_id=instance.id,
                        journey_id=instance.journey_id,
                        lead_id=int(lead_id),
                        node_id=None,
                        event_type=CommunicationEventType.JOURNEY_STARTED.value,
                        payload={"trigger_stage_key": stage_key, "journey_name": journey.name},
                    )

                    # 4. Load the published FlowDefinition
                    flow_def = await self._load_flow_definition(journey)
                    if flow_def is None:
                        logger.error(
                            "Journey %s has no flow_definition_id — stopping execution for instance %s",
                            journey.id, instance.id,
                        )
                        continue

                    # 5. Build rich ExecutionContext
                    ctx_dict: Dict[str, Any] = {
                        "trigger_stage_key": stage_key,
                        "flow_definition_id": str(flow_def.id),
                    }
                    node_outputs: Dict[str, Any] = {}
                    exec_ctx = ExecutionContext(
                        lead_id=int(lead_id),
                        lead=lead_context.get("lead", {}),
                        company=lead_context.get("company"),
                        journey_name=journey.name or "",
                        instance_id=str(instance.id),
                        flow_definition_id=str(flow_def.id),
                        execution_time=execution_time,
                        node_outputs=node_outputs,
                        context=ctx_dict,
                    )
                    # Wire resolver and renderer AFTER creation (circular ref not needed)
                    resolver = VariableResolverService(exec_ctx.to_dict())
                    renderer = TemplateRendererService(resolver)
                    object.__setattr__(exec_ctx, "resolver", resolver)
                    object.__setattr__(exec_ctx, "renderer", renderer)
                    object.__setattr__(exec_ctx, "template_service", TemplateService(session))
                    # Lets send_whatsapp_executor.py/send_email_executor.py
                    # reserve a journey-send idempotency key on the same
                    # session/transaction the engine already uses for this
                    # instance — see journey_send_idempotency_service.py.
                    object.__setattr__(exec_ctx, "session", session)

                    # 6. Resolve the first node (trigger) and execute it
                    first_node_id = self._resolve_first_node(flow_def.definition)

                    trigger_node = self._find_node_by_id(flow_def.definition, first_node_id)
                    if trigger_node:
                        continue_traversal = await self._execute_node(
                            node=trigger_node,
                            instance=instance,
                            flow_def_id=str(flow_def.id),
                            lead_id=int(lead_id),
                            context=ctx_dict,
                            exec_ctx=exec_ctx,
                            log_service=log_service,
                            instance_service=instance_service,
                            event_service=event_service,
                        )

                        # 7. Traverse remaining nodes only if trigger succeeded
                        if continue_traversal:
                            await self._traverse_flow(
                                definition=flow_def.definition,
                                instance=instance,
                                flow_def_id=str(flow_def.id),
                                lead_id=int(lead_id),
                                start_node_id=first_node_id,
                                context=ctx_dict,
                                exec_ctx=exec_ctx,
                                log_service=log_service,
                                instance_service=instance_service,
                                event_service=event_service,
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
    # Node execution dispatcher
    # ------------------------------------------------------------------

    async def _execute_node(
        self,
        node: Dict[str, Any],
        instance: Any,
        flow_def_id: str,
        lead_id: int,
        context: Dict[str, Any],
        log_service: FlowExecutionLogService,
        instance_service: RunningInstanceService,
        event_service: CommunicationEventService,
        exec_ctx: Optional[ExecutionContext] = None,
    ) -> bool:
        """Execute a single node through its registered executor.

        Creates Started → Success|Failed execution logs with duration.
        Updates the running instance's data with current_node_id and
        last_executed_at.

        Returns:
            True if traversal should continue to the next node.
            False if traversal should stop (failure or end node reached).
        """
        node_id = node.get("id", "")
        node_type = node.get("type", "")
        started_at = datetime.utcnow()

        # ── Started log ──────────────────────────────────────────────
        await log_service.create(
            FlowExecutionLogCreateSchema(
                flow_definition_id=flow_def_id,
                running_instance_id=instance.id,
                lead_id=lead_id,
                node_id=node_id,
                status="started",
                input={"node_type": node_type},
                output={},
            )
        )

        # ── Resolve executor ────────────────────────────────────────
        try:
            executor = ExecutorFactory.get(node_type)
        except ValueError:
            logger.error("Unknown node type %s for node %s", node_type, node_id)
            await self._create_failed_log(
                log_service, flow_def_id, instance.id, lead_id,
                node_id, node_type, f"Unknown node type: {node_type}", started_at,
            )
            await instance_service.fail(UUID(instance.id))
            return False

        # ── Dispatch to executor ────────────────────────────────────
        try:
            result = await executor.execute(node, instance, lead_id, context, exec_ctx=exec_ctx)
        except Exception as exc:
            logger.exception("Executor %s raised exception for node %s", node_type, node_id)
            await self._create_failed_log(
                log_service, flow_def_id, instance.id, lead_id,
                node_id, node_type, str(exc), started_at,
            )
            await instance_service.fail(UUID(instance.id))
            return False

        completed_at = datetime.utcnow()
        duration_ms = int((completed_at - started_at).total_seconds() * 1000)

        # ── Handle result ───────────────────────────────────────────
        if result.success:
            output_data = result.output or {}
            output_data.pop("log_payload", None)

            await self._record_communication_event(
                event_service=event_service,
                running_instance_id=instance.id,
                journey_id=getattr(instance, "journey_id", None),
                lead_id=lead_id,
                node_id=node_id,
                node_type=node_type,
                payload=output_data,
            )

            # Success log
            await log_service.create(
                FlowExecutionLogCreateSchema(
                    flow_definition_id=flow_def_id,
                    running_instance_id=instance.id,
                    lead_id=lead_id,
                    node_id=node_id,
                    status="success",
                    input={
                        "node_type": node_type,
                        "started_at": started_at.isoformat(),
                    },
                    output={
                        "completed_at": completed_at.isoformat(),
                        "duration_ms": duration_ms,
                        **output_data,
                    },
                )
            )

            # Update execution context
            if result.updated_context:
                context.update(result.updated_context)
                if exec_ctx and exec_ctx.context:
                    exec_ctx.context.update(result.updated_context)

            # Store node output for downstream variable resolution
            if exec_ctx and exec_ctx.node_outputs is not None:
                exec_ctx.node_outputs[str(node_id)] = output_data

            # Update running instance — store current node tracking
            # in the JSON data column (no schema migration needed)
            current_data = dict(instance.data or {})
            current_data["current_node_id"] = node_id
            current_data["last_executed_at"] = completed_at.isoformat()

            # Handle skipped (pause/wait/delay/approval/task) nodes — stop traversal
            if result.status == "skipped":
                updated_ctx = result.updated_context or {}
                halt = updated_ctx.get("_halt")
                resume_at = updated_ctx.get("resume_at")

                if halt == "approval":
                    approval_data = updated_ctx.get("_approval_data")
                    if approval_data:
                        approvals = current_data.get("approvals") or {}
                        approvals[approval_data["id"]] = approval_data
                        current_data["approvals"] = approvals
                        current_data["current_approval_id"] = approval_data["id"]
                    current_data["_pause_reason"] = "approval"
                    current_data["_pause_node_id"] = updated_ctx.get("_halt_node_id", node_id)
                    await instance_service.wait_approval(UUID(instance.id), current_data)
                    logger.info("Approval node %s — waiting for approval %s", node_id, updated_ctx.get("approval_id"))
                elif halt == "task":
                    task_data = updated_ctx.get("_task_data")
                    if task_data:
                        tasks = current_data.get("tasks") or {}
                        tasks[task_data["id"]] = task_data
                        current_data["tasks"] = tasks
                        current_data["current_task_id"] = task_data["id"]
                    current_data["_pause_reason"] = "task"
                    current_data["_pause_node_id"] = updated_ctx.get("_halt_node_id", node_id)
                    await instance_service.wait_task(UUID(instance.id), current_data)
                    logger.info("ManualTask node %s — waiting for task %s", node_id, updated_ctx.get("task_id"))
                elif resume_at:
                    current_data["resume_at"] = resume_at
                    if updated_ctx.get("_wait"):
                        await instance_service.wait(UUID(instance.id), current_data)
                        logger.info("Wait node %s paused until %s", node_id, resume_at)
                    else:
                        await instance_service.update(
                            UUID(instance.id), RunningInstanceUpdateSchema(data=current_data),
                        )
                        logger.info("Delay node %s paused until %s", node_id, resume_at)
                elif updated_ctx.get("_wait_condition"):
                    # Event-based Wait (replied/stage_changed/field_condition/
                    # webhook_event) — no resume_at at all; reuses the
                    # existing "waiting" status (no new InstanceStatus value,
                    # no migration) so the scheduler's existing find_waiting-
                    # style query pattern extends cleanly via
                    # RunningInstanceService.find_due_events(). Resolved by
                    # wait_condition_service.py (scheduler poll) or, for
                    # webhook_event, the dedicated trigger-event route —
                    # both ultimately call engine.resume_instance(), same as
                    # every other pause type here.
                    current_data["wait_condition"] = updated_ctx["_wait_condition"]
                    current_data["_pause_reason"] = "event"
                    current_data["_pause_node_id"] = node_id
                    await instance_service.wait(UUID(instance.id), current_data)
                    logger.info(
                        "Wait node %s paused on event condition %s",
                        node_id, updated_ctx["_wait_condition"],
                    )
                else:
                    # Plain skip with no special handling — just update data
                    await instance_service.update(
                        UUID(instance.id), RunningInstanceUpdateSchema(data=current_data),
                    )
                return False

            # Normal success — persist data and continue
            await instance_service.update(
                UUID(instance.id),
                RunningInstanceUpdateSchema(data=current_data),
            )
            instance.data = current_data

            # End node — mark completed and stop traversal
            if node_type == "end":
                await instance_service.complete(UUID(instance.id))
                return False

            return True

        # Executor reported failure
        await self._create_failed_log(
            log_service, flow_def_id, instance.id, lead_id,
            node_id, node_type, result.error or "Unknown error", started_at,
        )
        await instance_service.fail(UUID(instance.id))
        return False

    async def _create_failed_log(
        self,
        log_service: FlowExecutionLogService,
        flow_def_id: str,
        instance_id: str,
        lead_id: int,
        node_id: str,
        node_type: str,
        error_message: str,
        started_at: datetime,
    ) -> None:
        """Create a failed execution log with computed duration."""
        completed_at = datetime.utcnow()
        duration_ms = int((completed_at - started_at).total_seconds() * 1000)
        await log_service.create(
            FlowExecutionLogCreateSchema(
                flow_definition_id=flow_def_id,
                running_instance_id=instance_id,
                lead_id=lead_id,
                node_id=node_id,
                status="failed",
                input={
                    "node_type": node_type,
                    "started_at": started_at.isoformat(),
                },
                output={
                    "completed_at": completed_at.isoformat(),
                    "duration_ms": duration_ms,
                },
                error_message=error_message,
            )
        )

    async def _record_communication_event(
        self,
        event_service: CommunicationEventService,
        running_instance_id: str,
        journey_id: Optional[str],
        lead_id: int,
        node_id: Optional[str],
        payload: Optional[Dict[str, Any]] = None,
        node_type: Optional[str] = None,
        event_type: Optional[str] = None,
    ) -> None:
        """Record one row in the canonical communication-event log.

        Resolves ``event_type`` from ``node_type`` via
        ``_NODE_TYPE_TO_EVENT_TYPE`` when not given explicitly (the common
        case, called once per successful node execution from
        ``_execute_node``); silently no-ops for node types with no mapped
        event (delay/end/approval/etc — out of Sprint 1 scope). Callers with
        a fixed event (e.g. Journey Started) pass ``event_type`` directly.

        Best-effort: never raises, so a communication-event write failure
        can never fail journey execution — this log is observability, not
        the source of truth for traversal (that remains FlowExecutionLog /
        RunningJourneyInstance).
        """
        resolved_event_type = event_type or _NODE_TYPE_TO_EVENT_TYPE.get(node_type or "")
        if not resolved_event_type:
            return

        channel = _NODE_TYPE_TO_CHANNEL.get(node_type or "", CommunicationEventChannel.SYSTEM.value)
        payload = payload or {}
        provider_response = payload.get("provider_response") if isinstance(payload, dict) else None
        # A provider can return HTTP 200 with a soft-failure body (e.g.
        # JAWIS success:false, message_id:"") — "" is not a real message id
        # and must never be stored as one: uq_communication_events_pmid_event_type
        # only treats NULLs as distinct from each other (real, non-null ids
        # still dedupe correctly), so two empty-string sends of the same
        # event_type collide on commit. `or None` normalizes any falsy id
        # (including "") to NULL, matching an id-less/failed send.
        provider_message_id = None
        if isinstance(provider_response, dict):
            provider_message_id = provider_response.get("message_id") or None
            if provider_response.get("success") is False:
                payload = {**payload, "status": "failed"}

        try:
            await event_service.create(
                CommunicationEventCreateSchema(
                    running_instance_id=running_instance_id,
                    journey_id=journey_id,
                    lead_id=lead_id,
                    node_id=node_id,
                    event_type=resolved_event_type,
                    channel=channel,
                    provider_message_id=provider_message_id,
                    payload=payload,
                )
            )
        except IntegrityError:
            # A duplicate (provider_message_id, event_type) pair — pre-fix,
            # repeat empty-string sends; going forward, a genuine concurrent
            # duplicate real id. Must roll back: the failed INSERT leaves
            # this session's transaction aborted, and every later query on
            # it (this node's own "success" FlowExecutionLog, right after
            # this call returns) would otherwise fail too. A duplicate
            # status event is idempotent, not a journey failure.
            await event_service.repo.session.rollback()
            logger.warning(
                "Duplicate communication event (event_type=%s node_id=%s instance=%s provider_message_id=%s) "
                "— idempotent no-op",
                resolved_event_type, node_id, running_instance_id, provider_message_id,
            )
        except Exception:
            logger.exception(
                "Failed to record communication event (event_type=%s node_id=%s instance=%s)",
                resolved_event_type, node_id, running_instance_id,
            )

    # ------------------------------------------------------------------
    # Flow traversal
    # ------------------------------------------------------------------

    async def _traverse_flow(
        self,
        definition: Dict[str, Any],
        instance: Any,
        flow_def_id: str,
        lead_id: int,
        start_node_id: str,
        context: Dict[str, Any],
        log_service: FlowExecutionLogService,
        instance_service: RunningInstanceService,
        event_service: CommunicationEventService,
        exec_ctx: Optional[ExecutionContext] = None,
    ) -> None:
        """Walk through the flow graph dispatching every node to its executor.

        Builds an adjacency list from ``definition["edges"]`` and BFS-traverses
        starting from the neighbours of *start_node_id* (the trigger node was
        already executed by the caller).

        Traversal stops when:
        * An end node is reached (executor returns ``next_node_id=None``).
        * Any executor fails.
        """
        nodes = definition.get("nodes") or []
        edges = definition.get("edges") or []

        node_map: Dict[str, Any] = {n["id"]: n for n in nodes}

        # Build adjacency: source node -> list of target node IDs
        adjacency: Dict[str, list] = {}
        for edge in edges:
            src = edge.get("from") or edge.get("source")
            tgt = edge.get("to") or edge.get("target")
            if src and tgt:
                adjacency.setdefault(src, []).append(tgt)

        queue: list = list(adjacency.get(start_node_id, []))
        visited: set = {start_node_id}

        while queue:
            node_id = queue.pop(0)
            if node_id in visited:
                continue
            visited.add(node_id)

            node = node_map.get(node_id)
            if not node:
                continue

            should_continue = await self._execute_node(
                node=node,
                instance=instance,
                flow_def_id=flow_def_id,
                lead_id=lead_id,
                context=context,
                exec_ctx=exec_ctx,
                log_service=log_service,
                instance_service=instance_service,
                event_service=event_service,
            )

            if not should_continue:
                return

            next_nodes = adjacency.get(node_id, [])
            queue.extend(next_nodes)

    # ------------------------------------------------------------------
    # Resume & Retry
    # ------------------------------------------------------------------

    async def resume_instance(self, instance_id: UUID) -> bool:
        """Resume a waiting instance from its ``current_node_id``.

        The current node (wait/delay) is **skipped** — traversal continues
        to its downstream neighbours.  Used by :class:`SchedulerService`.
        """
        return await self._resume_from(instance_id, skip_current=True)

    async def retry_node(self, instance_id: UUID) -> bool:
        """Re-execute the failed node and continue traversal.

        ``instance.data.retry_count`` is incremented by the caller
        (:class:`RetryService`).  The current node is re-executed.
        """
        return await self._resume_from(instance_id, skip_current=False)

    async def retry_journey(self, instance_id: UUID) -> bool:
        """Restart the entire journey from the trigger node.

        ``instance.data.current_node_id`` is set to *None* by the caller
        so that the trigger node is resolved as the starting point.
        """
        return await self._resume_from(instance_id, skip_current=False)

    async def _resume_from(self, instance_id: UUID, skip_current: bool) -> bool:
        """Shared resume logic used by the scheduler and retry flows.

        When *skip_current* is True the node at ``current_node_id`` is
        skipped (traversal begins at its neighbours).  When False the
        node is re-executed first.
        """
        async with self._session_factory() as session:
            try:
                journey_service = JourneyService(session)
                instance_service = RunningInstanceService(session)
                log_service = FlowExecutionLogService(session)
                event_service = CommunicationEventService(session)
                lead_provider: LeadProvider = LeadProviderFactory.get_provider()

                # Row-locked read (SELECT ... FOR UPDATE) — see
                # RunningInstanceRepository.get_for_update's docstring.
                # Serializes concurrent resume attempts for the same
                # instance (a scheduler tick racing a manual/webhook resume,
                # or two scheduler processes) so the duplicate-resume guard
                # below can reliably tell whether it's the first or a
                # subsequent caller.
                instance = await instance_service.get_for_update(instance_id)
                journey = await journey_service.get(UUID(instance.journey_id))

                flow_def = await self._load_flow_definition(journey)
                if flow_def is None:
                    return False

                instance_data = dict(instance.data or {})

                # Idempotency guard — only meaningful for the scheduler/
                # webhook resume path (skip_current=True); retries are
                # explicit user actions and always proceed regardless. If a
                # concurrent caller already claimed and cleared this
                # instance's time/event pause markers before we acquired the
                # row lock above, there's nothing left for THIS caller to
                # do — returning early avoids double-traversing (double
                # sends, double stage changes, etc.). Approval/task pauses
                # are identified by `_pause_reason` and never rely on
                # resume_at/wait_condition, so they're untouched by this
                # check.
                pause_reason = instance_data.get("_pause_reason")
                if (
                    skip_current
                    and pause_reason not in ("approval", "task")
                    and not instance_data.get("resume_at")
                    and not instance_data.get("wait_condition")
                    and instance_data.get("current_node_id")
                ):
                    logger.info(
                        "Engine._resume_from: instance %s has no pending resume_at/"
                        "wait_condition (already resumed by a concurrent caller) — "
                        "skipping duplicate resume",
                        instance_id,
                    )
                    return True

                lead_context = await lead_provider.get_lead_context(instance.lead_id)
                execution_time = datetime.utcnow()
                ctx_dict: Dict[str, Any] = {
                    "trigger_stage_key": instance_data.get("trigger_stage_key", "unknown"),
                    "flow_definition_id": str(flow_def.id),
                }
                ctx_dict.update(instance_data)
                node_outputs: Dict[str, Any] = {}

                exec_ctx = ExecutionContext(
                    lead_id=instance.lead_id,
                    lead=lead_context.get("lead", {}),
                    company=lead_context.get("company"),
                    journey_name=journey.name or "",
                    instance_id=str(instance.id),
                    flow_definition_id=str(flow_def.id),
                    execution_time=execution_time,
                    node_outputs=node_outputs,
                    context=ctx_dict,
                )
                resolver = VariableResolverService(exec_ctx.to_dict())
                renderer = TemplateRendererService(resolver)
                object.__setattr__(exec_ctx, "resolver", resolver)
                object.__setattr__(exec_ctx, "renderer", renderer)
                object.__setattr__(exec_ctx, "template_service", TemplateService(session))
                # See the matching comment in _execute_for_stage — same
                # journey-send idempotency wiring for resume/retry.
                object.__setattr__(exec_ctx, "session", session)

                # Determine starting node
                start_node_id = instance_data.get("current_node_id")
                if not start_node_id:
                    start_node_id = self._resolve_first_node(flow_def.definition)

                start_node = self._find_node_by_id(flow_def.definition, start_node_id)
                if not start_node:
                    logger.error(
                        "Resume start node %s not found for instance %s",
                        start_node_id, instance_id,
                    )
                    await instance_service.fail(instance_id)
                    return False

                # Clean up resume metadata from instance data. wait_condition/
                # the "event" pause markers are only ever set by the new
                # event-based Wait branch (engine.py's _wait_condition
                # handling) — popping them here is a no-op for every other
                # pause type (approval/task pop their own differently-named
                # markers themselves, before calling resume_instance()).
                clean_data = dict(instance_data)
                clean_data.pop("resume_at", None)
                clean_data.pop("wait_condition", None)
                if clean_data.get("_pause_reason") == "event":
                    clean_data.pop("_pause_reason", None)
                    clean_data.pop("_pause_node_id", None)

                if skip_current:
                    if start_node.get("type") == "wait":
                        await self._record_communication_event(
                            event_service=event_service,
                            running_instance_id=instance.id,
                            journey_id=instance.journey_id,
                            lead_id=instance.lead_id,
                            node_id=start_node_id,
                            event_type=CommunicationEventType.WAIT_COMPLETED.value,
                            payload={"resumed_at": datetime.utcnow().isoformat()},
                        )

                    # Schedule mode: skip current node, traverse from neighbours
                    # First update instance data to remove resume_at
                    await instance_service.update(
                        instance_id, RunningInstanceUpdateSchema(data=clean_data),
                    )
                    await self._traverse_flow(
                        definition=flow_def.definition,
                        instance=instance,
                        flow_def_id=str(flow_def.id),
                        lead_id=instance.lead_id,
                        start_node_id=start_node_id,
                        context=ctx_dict,
                        exec_ctx=exec_ctx,
                        log_service=log_service,
                        instance_service=instance_service,
                        event_service=event_service,
                    )
                else:
                    # Retry mode: execute the current node then traverse
                    continue_traversal = await self._execute_node(
                        node=start_node,
                        instance=instance,
                        flow_def_id=str(flow_def.id),
                        lead_id=instance.lead_id,
                        context=ctx_dict,
                        exec_ctx=exec_ctx,
                        log_service=log_service,
                        instance_service=instance_service,
                        event_service=event_service,
                    )
                    if continue_traversal:
                        await self._traverse_flow(
                            definition=flow_def.definition,
                            instance=instance,
                            flow_def_id=str(flow_def.id),
                            lead_id=instance.lead_id,
                            start_node_id=start_node_id,
                            context=ctx_dict,
                            exec_ctx=exec_ctx,
                            log_service=log_service,
                            instance_service=instance_service,
                            event_service=event_service,
                        )

                return True

            except Exception as exc:
                logger.exception(
                    "Engine._resume_from error for instance %s: %s", instance_id, exc,
                )
                return False

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

    @staticmethod
    def _find_node_by_id(definition: Dict[str, Any], node_id: str) -> Optional[Dict[str, Any]]:
        """Return the node dict matching *node_id*, or None."""
        nodes = definition.get("nodes") if definition else []
        for node in nodes:
            if node.get("id") == node_id:
                return node
        return None

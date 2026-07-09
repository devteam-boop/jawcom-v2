"""Lead-scoped Journey control — consumed by JAWIS (Decision 4).

Thin wrappers over the EXISTING Journey/RunningInstance services — no
start/pause/resume/status logic is reimplemented here. Protected by
JawisAuthMiddleware (path pattern /api/leads/*/journey/*).

POST /api/leads/{lead_id}/journey/pause is intentionally NOT implemented —
see the audit note below and the readiness report. No stub, no placeholder
route left behind for it.
"""

from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session
from app.database.session import async_session_maker
from app.models.communication_event import CommunicationEventChannel, CommunicationEventType
from app.communication_events.schemas import CommunicationEventCreateSchema
from app.repositories.running_instance_repository import RunningInstanceRepository
from app.runtime.schemas import RunningInstanceCreateSchema, RunningInstanceSchema
from app.services.communication_event_service import CommunicationEventService
from app.services.running_instance_service import RunningInstanceService

router = APIRouter(prefix="/api/leads", tags=["Lead Journey Control"])


class JourneyStartRequest(BaseModel):
    journey_id: str
    # Required — see Decision 1 / EmailSendRequest.stage. JawCom persists
    # this as-is; never looked up via get_lead_context() or any CRM call.
    stage: str
    data: Dict[str, Any] = Field(default_factory=dict)


@router.post(
    "/{lead_id}/journey/start",
    response_model=RunningInstanceSchema,
    status_code=201,
    summary="Start a journey for a lead (lead-scoped wrapper)",
    description="Delegates to RunningInstanceService.create() — the existing "
                "'start a journey instance for a lead' primitive. Also records "
                "the supplied stage into communication_events (journey_started).",
)
async def start_lead_journey(
    lead_id: int,
    request: JourneyStartRequest,
    db: AsyncSession = Depends(get_db_session),
):
    service = RunningInstanceService(db)
    try:
        instance = await service.create(
            RunningInstanceCreateSchema(
                lead_id=lead_id,
                journey_id=request.journey_id,
                data=request.data,
            )
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    event_service = CommunicationEventService(db)
    await event_service.create(
        CommunicationEventCreateSchema(
            running_instance_id=instance.id,
            journey_id=request.journey_id,
            lead_id=lead_id,
            event_type=CommunicationEventType.JOURNEY_STARTED.value,
            channel=CommunicationEventChannel.SYSTEM.value,
            payload={"stage": request.stage, "data": request.data},
        )
    )

    return instance


@router.post(
    "/{lead_id}/journey/resume",
    response_model=RunningInstanceSchema,
    summary="Resume a lead's waiting journey instance (lead-scoped wrapper)",
    description="Finds the lead's current waiting instance and delegates to "
                "the existing ExecutionEngine.resume_instance() — same logic "
                "POST /api/running-instances/{instance_id}/resume already uses.",
)
async def resume_lead_journey(
    lead_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    repo = RunningInstanceRepository(db)
    instances = await repo.get_by_lead(lead_id)
    waiting_statuses = {"waiting", "waiting_approval", "waiting_task"}
    instance = next((i for i in instances if i.status in waiting_statuses), None)
    if instance is None:
        raise HTTPException(status_code=404, detail=f"No waiting journey instance found for lead {lead_id}")

    from app.execution.engine import ExecutionEngine

    engine = ExecutionEngine(async_session_maker)
    try:
        await engine.resume_instance(instance.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    service = RunningInstanceService(db)
    return await service.get(instance.id)


@router.get(
    "/{lead_id}/journey/status",
    response_model=Optional[RunningInstanceSchema],
    summary="Current journey status for a lead (lead-scoped wrapper)",
    description="Returns the lead's most recent running instance (delegates to "
                "RunningInstanceRepository.get_by_lead()), or null if the lead "
                "has never had a journey instance.",
)
async def get_lead_journey_status(
    lead_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    service = RunningInstanceService(db)
    instances = await service.list(lead_id=lead_id, limit=1)
    return instances[0] if instances else None

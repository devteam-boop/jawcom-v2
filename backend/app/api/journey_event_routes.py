"""Journey Event Routes — external trigger for the "webhook_event" Wait type.

Mirrors approval_routes.py's exact shape (the established pattern for "an
external actor resumes a specific waiting instance"): verify the instance is
actually waiting on the posted event_key, then call
ExecutionEngine.resume_instance() directly — no new resume mechanism.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session
from app.database.session import async_session_maker
from app.services.running_instance_service import RunningInstanceService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/journeys/instances",
    tags=["Journey Events"],
    responses={404: {"description": "Not found"}},
)


class TriggerEventRequest(BaseModel):
    event_key: str = Field(..., description="Must match the wait node's configured event_key")
    payload: dict = Field(default_factory=dict, description="Arbitrary caller-supplied event payload (logged only)")


@router.post("/{instance_id}/trigger-event", response_model=dict)
async def trigger_event(
    instance_id: UUID,
    request: TriggerEventRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Resume an instance paused on ``wait_type == "webhook_event"`` — the
    only Wait event type not detected by the scheduler's poll loop (every
    other event type is checked by wait_condition_service.py each tick;
    this one is push-only by design, since "an external webhook/event
    occurred" has no natural poll target)."""
    instance_service = RunningInstanceService(db)
    try:
        instance = await instance_service.get(instance_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    wait_condition = (instance.data or {}).get("wait_condition") or {}
    if wait_condition.get("type") != "webhook_event":
        raise HTTPException(
            status_code=409,
            detail=f"Instance {instance_id} is not waiting on a webhook_event condition",
        )
    if wait_condition.get("event_key") != request.event_key:
        raise HTTPException(
            status_code=409,
            detail=f"event_key {request.event_key!r} does not match the instance's "
                   f"configured event_key {wait_condition.get('event_key')!r}",
        )

    logger.info(
        "trigger_event: instance=%s lead_id=%s event_key=%s payload=%s",
        instance_id, instance.lead_id, request.event_key, request.payload,
    )

    from app.execution.engine import ExecutionEngine
    engine = ExecutionEngine(async_session_maker)
    success = await engine.resume_instance(instance_id)
    return {"resumed": success, "event_key": request.event_key}

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.communication_events.schemas import CommunicationEventSchema
from app.core.dependencies import get_db_session
from app.services.communication_event_service import CommunicationEventService

# No POST endpoint here by design: communication events are created only
# internally, by ExecutionEngine._record_communication_event() and
# TaskService.complete_task(). There is no public/production API to create
# one directly — this router is read-only.
router = APIRouter(
    prefix="/api/communication-events",
    tags=["Communication Events"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[CommunicationEventSchema],
            summary="List communication events",
            description="Returns paginated communication events in chronological order, "
                        "optionally filtered by running instance, journey, lead, or event type.")
async def list_communication_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    running_instance_id: Optional[UUID] = Query(None, description="Filter by running instance ID"),
    journey_id: Optional[UUID] = Query(None, description="Filter by journey ID"),
    lead_id: Optional[int] = Query(None, description="Filter by lead ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    db: AsyncSession = Depends(get_db_session),
):
    service = CommunicationEventService(db)
    return await service.list(
        skip=skip, limit=limit,
        running_instance_id=running_instance_id,
        journey_id=journey_id,
        lead_id=lead_id,
        event_type=event_type,
    )


@router.get("/{event_id}", response_model=CommunicationEventSchema,
            summary="Get communication event by ID")
async def get_communication_event(
    event_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    service = CommunicationEventService(db)
    try:
        return await service.get(event_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

"""Public timeline endpoint — consumed by JAWIS.

GET /api/leads/{lead_id}/timeline returns every communication_events row
for a lead (email, WhatsApp, and any other channel/system event) in
chronological order — manual and automation together, no special-casing.
Reuses CommunicationEventService.list() exactly as the existing
/api/communication-events endpoint does; no new table, no new schema,
no duplicated storage.
"""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.communication_events.schemas import CommunicationEventSchema
from app.core.dependencies import get_db_session
from app.services.communication_event_service import CommunicationEventService

router = APIRouter(prefix="/api/leads", tags=["Lead Timeline"])


@router.get(
    "/{lead_id}/timeline",
    response_model=List[CommunicationEventSchema],
    summary="Full communication timeline for a lead (email, WhatsApp, journey, system)",
    description="Every communication_events row for this lead, chronological, "
                "manual and automation sends together. Consumed by JAWIS.",
)
async def get_lead_timeline(
    lead_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    service = CommunicationEventService(db)
    return await service.list(lead_id=lead_id, limit=500)

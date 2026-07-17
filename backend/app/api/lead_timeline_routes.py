"""Public timeline endpoint — consumed by JAWIS.

GET /api/leads/{lead_id}/timeline returns every communication_events row
for a lead (email, WhatsApp, and any other channel/system event) in
chronological order — manual and automation together, no special-casing.
Reuses CommunicationEventService.list() exactly as the existing
/api/communication-events endpoint does; no new table, no new schema,
no duplicated storage.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.communication_events.schemas import CommunicationEventSchema
from app.core.dependencies import get_db_session
from app.services.communication_event_service import CommunicationEventService
from app.jawis.client import get_jawis_client, JawisApiError
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

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


class LeadSummaryResponse(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    stage: Optional[str] = None


@router.get(
    "/{lead_id}/summary",
    response_model=LeadSummaryResponse,
    summary="Lightweight lead identity (name/phone/email/stage) for the Inbox/Contacts UI",
    description="Thin read-only wrapper around the existing JawisClient.get_lead() "
                "(already used server-side by app/api/message_routes.py) — no new "
                "external integration, just exposes that same lookup over HTTP so "
                "the frontend can show a real name/phone/email instead of only "
                "'Lead #<id>'. JAWIS no longer returns company/assigned_user on this "
                "lookup (see JawisClient.get_lead docstring) — not included here either, "
                "not fabricated.",
)
async def get_lead_summary(lead_id: int):
    client = get_jawis_client()
    try:
        lead = await client.get_lead(str(lead_id))
    except JawisApiError as exc:
        logger.error("get_lead_summary: JAWIS unreachable for lead_id=%s: %s", lead_id, exc)
        raise HTTPException(status_code=502, detail="JAWIS is unreachable — lead identity unavailable")
    if lead is None:
        raise HTTPException(status_code=404, detail=f"Lead {lead_id} not found")
    return LeadSummaryResponse(
        id=lead.id, name=lead.name, email=lead.email, phone=lead.phone,
        city=lead.city, stage=lead.stage,
    )

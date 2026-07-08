from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_assistant.schemas import AILeadAssistantResult
from app.core.dependencies import get_db_session
from app.services.ai_lead_assistant_service import (
    AILeadAssistantService,
    AIAssistantNotConfiguredError,
    AIAssistantProviderError,
)

router = APIRouter(prefix="/api/leads", tags=["AI Assistant"])


@router.get("/{lead_id}/ai-assistant", response_model=AILeadAssistantResult,
            summary="Generate the AI Lead Assistant for a lead",
            description="Summary, next-best-action, reply suggestion (if applicable), "
                        "and lead health — generated fresh on each call from existing "
                        "communication events, journeys, and tasks. Not persisted.")
async def get_ai_lead_assistant(
    lead_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    service = AILeadAssistantService(db)
    try:
        return await service.generate(lead_id)
    except AIAssistantNotConfiguredError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except AIAssistantProviderError as e:
        raise HTTPException(status_code=502, detail=str(e))

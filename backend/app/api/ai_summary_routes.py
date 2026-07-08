from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session
from app.services.ai_lead_summary_service import (
    AILeadSummaryService,
    AIAssistantNotConfiguredError,
    AIAssistantProviderError,
)

router = APIRouter(prefix="/api/leads", tags=["AI Summary"])


@router.get("/{lead_id}/ai-summary",
            summary="Generate a lightweight AI Lead Summary",
            description="Read-only, on-demand summary generated from existing "
                        "communication events, flow execution logs, running "
                        "instances, tasks, and notes. Not cached, not persisted. "
                        "Returns {\"status\": \"ai_unavailable\"} if the AI "
                        "provider is not configured or the call fails.")
async def get_ai_lead_summary(
    lead_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    service = AILeadSummaryService(db)
    try:
        result = await service.generate(lead_id)
        return result
    except AIAssistantNotConfiguredError:
        return {"status": "ai_unavailable"}
    except AIAssistantProviderError:
        return {"status": "ai_unavailable"}

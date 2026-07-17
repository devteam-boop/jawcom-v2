from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.ai_text_transform_service import (
    AITextTransformService,
    AIAssistantNotConfiguredError,
    AIAssistantProviderError,
)

router = APIRouter(prefix="/api/ai", tags=["AI Text Transform"])

_VALID_ACTIONS = {"rewrite", "shorten", "professional", "friendly", "translate"}


class TransformRequest(BaseModel):
    text: str
    action: str
    target_language: Optional[str] = None


class TransformResponse(BaseModel):
    text: str


@router.post(
    "/transform",
    response_model=TransformResponse,
    summary="Rewrite/shorten/translate/change tone of a composer draft (Claude)",
)
async def transform_text(request: TransformRequest):
    if request.action not in _VALID_ACTIONS:
        raise HTTPException(status_code=400, detail=f"action must be one of {sorted(_VALID_ACTIONS)}")
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="text is required")

    service = AITextTransformService()
    try:
        result = await service.transform(request.text, request.action, request.target_language)
    except AIAssistantNotConfiguredError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except AIAssistantProviderError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return TransformResponse(text=result)

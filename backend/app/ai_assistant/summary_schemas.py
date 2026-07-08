from typing import List, Literal

from pydantic import BaseModel, ConfigDict, Field

LeadHealth = Literal["Hot", "Warm", "Cold"]


class AILeadSummaryResult(BaseModel):
    """Structured output contract for the lightweight AI Lead Summary
    (GET /api/leads/{lead_id}/ai-summary). Distinct from, and simpler than,
    AILeadAssistantResult (app/ai_assistant/schemas.py) — separate endpoint,
    separate response shape, per this feature's own spec.
    """
    model_config = ConfigDict(extra="forbid")

    summary: List[str] = Field(
        description="At most 6 concise bullet points covering communication "
                     "events, notes, and tasks for this lead.",
    )
    journey_summary: str = Field(
        description="One short paragraph summarizing journey/automation progress "
                     "for this lead.",
    )
    next_best_action: str = Field(
        description="A short, specific recommended next action for this lead.",
    )
    reason: str = Field(
        description="A short explanation of why this action was recommended.",
    )
    lead_health: LeadHealth = Field(
        description="Overall lead health based on journey and communication history.",
    )

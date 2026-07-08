from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

# Fixed action vocabulary from the task spec — the model must pick exactly one.
NextBestAction = Literal[
    "call",
    "whatsapp",
    "email",
    "schedule_visit",
    "send_proposal",
    "follow_up",
    "close_lost",
    "mark_qualified",
]

LeadHealth = Literal["hot", "warm", "cold"]


class AILeadAssistantResult(BaseModel):
    """Structured output contract for the AI Lead Assistant.

    ``extra="forbid"`` makes Pydantic emit ``additionalProperties: false`` in
    the generated JSON schema, which the Claude API's structured-outputs
    feature (``output_config.format``) requires on every object.
    """
    model_config = ConfigDict(extra="forbid")

    summary: List[str] = Field(
        description="At most 6 concise bullet points summarizing communication "
                     "events, journey progress, notes, and tasks for this lead.",
    )
    next_best_action: NextBestAction = Field(
        description="The single most useful next action for this lead.",
    )
    next_best_action_reason: str = Field(
        description="A short explanation of why this action was chosen.",
    )
    reply_suggestion: Optional[str] = Field(
        default=None,
        description="A suggested reply to send the lead. Only populate this "
                     "when the latest communication event's channel is "
                     "whatsapp or email; otherwise leave it null.",
    )
    lead_health: LeadHealth = Field(
        description="Overall lead health classification based on journey history.",
    )

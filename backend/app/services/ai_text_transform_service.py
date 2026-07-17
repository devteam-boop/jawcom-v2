"""Generic draft-text transforms for the Inbox composer (Phase 3, Task 5) —
Rewrite / Shorten / Translate / Professional tone / Friendly tone.

Distinct from AILeadAssistantService (per-lead context: summary/next-best-
action/reply suggestion) and AILeadSummaryService (per-lead summary only) —
those operate on a lead's communication history. This operates on the
agent's own draft text in the composer, which has no lead context to read.
Same Anthropic client/config/error-handling pattern as those two services;
no new integration.
"""

import logging

import anthropic

from app.config.settings import get_settings

logger = logging.getLogger(__name__)

_INSTRUCTIONS = {
    "rewrite": "Rewrite the following message to be clearer, keeping the same meaning and length roughly the same.",
    "shorten": "Shorten the following message as much as possible while keeping its core meaning.",
    "professional": "Rewrite the following message in a professional, business-appropriate tone.",
    "friendly": "Rewrite the following message in a warm, friendly, conversational tone.",
    "translate": "Translate the following message into {target_language}.",
}


class AIAssistantNotConfiguredError(Exception):
    """Raised when ANTHROPIC_API_KEY is not set."""


class AIAssistantProviderError(Exception):
    """Raised when the Claude API call itself fails."""


class AITextTransformService:
    def __init__(self):
        settings = get_settings()
        self._api_key = settings.ANTHROPIC_API_KEY
        self._model = settings.ANTHROPIC_MODEL

    async def transform(self, text: str, action: str, target_language: str = None) -> str:
        if not self._api_key:
            raise AIAssistantNotConfiguredError("AI text transform not configured (missing ANTHROPIC_API_KEY)")
        if action not in _INSTRUCTIONS:
            raise ValueError(f"Unknown action: {action!r}")

        instruction = _INSTRUCTIONS[action]
        if action == "translate":
            instruction = instruction.format(target_language=target_language or "English")

        client = anthropic.Anthropic(api_key=self._api_key)
        try:
            response = client.messages.create(
                model=self._model,
                max_tokens=2000,
                system=(
                    "You transform draft messages for a sales/support agent. "
                    "Reply with ONLY the transformed message text — no preamble, "
                    "no quotes, no explanation."
                ),
                messages=[{"role": "user", "content": f"{instruction}\n\n---\n{text}"}],
            )
        except anthropic.APIStatusError as exc:
            logger.error("AI text transform: Claude API error %s: %s", exc.status_code, exc.message)
            raise AIAssistantProviderError(f"Claude API error {exc.status_code}: {exc.message}") from exc
        except anthropic.APIConnectionError as exc:
            logger.error("AI text transform: Claude API unreachable: %s", exc)
            raise AIAssistantProviderError(f"Claude API unreachable: {exc}") from exc

        if response.stop_reason == "refusal":
            raise AIAssistantProviderError("Claude declined to transform this message")

        result = next((b.text for b in response.content if b.type == "text"), None)
        if not result:
            raise AIAssistantProviderError("Claude returned no text output")
        return result.strip()

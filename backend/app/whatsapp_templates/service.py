"""WhatsApp Template Management service (Phase 1, Features 2/3/4/6).

JawCom is the single source of truth for WhatsApp templates (see module
docstring on app/models/whatsapp_template.py): every row here originates
from sync_from_meta() — there is no create/update/delete path, matching
Feature 8 ("No dummy templates... Everything must come from Meta Sync").
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.providers.meta.meta_provider import MetaProvider
from app.repositories.whatsapp_template_repository import WhatsAppTemplateRepository
from app.models.whatsapp_template import WhatsAppTemplate
from app.models.email_sync_state import EmailSyncState
from .schemas import (
    WhatsAppTemplateSchema,
    WhatsAppTemplateSyncResultSchema,
    WhatsAppTemplatePreviewResponse,
)
from .exceptions import WhatsAppTemplateNotFoundError, MetaSyncError

# Reuses email_sync_state (app/models/email_sync_state.py) rather than a new
# single-purpose table — that model's own docstring already anticipates
# exactly this: "Keyed by sync_name so a second named sync could be added
# later without a schema change." This is that second named sync; the
# table's name predates this use and isn't renamed (out of scope, and Gmail
# sync still owns "gmail_inbox" in the same table).
_SYNC_NAME = "whatsapp_templates"

logger = logging.getLogger(__name__)

# Meta's own numbered placeholder convention ({{1}}, {{2}}, ...) — distinct
# from JawCom's Jinja2 {{name}} templates (app/templates/renderer.py). Not
# reused/mixed with that renderer: different system, different syntax.
_META_VARIABLE_PATTERN = re.compile(r"\{\{\s*(\d+)\s*\}\}")


def _extract_meta_variables(text: Optional[str]) -> List[str]:
    if not text:
        return []
    seen = []
    for match in _META_VARIABLE_PATTERN.findall(text):
        if match not in seen:
            seen.append(match)
    return seen


def _parse_components(components: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Map Meta's components[] array (HEADER/BODY/FOOTER/BUTTONS) onto our
    flat header_type/body/footer/buttons columns."""
    header_type = None
    body = ""
    footer = None
    buttons: List[Dict[str, Any]] = []

    for component in components or []:
        ctype = (component.get("type") or "").upper()
        if ctype == "HEADER":
            header_type = component.get("format")
        elif ctype == "BODY":
            body = component.get("text") or ""
        elif ctype == "FOOTER":
            footer = component.get("text")
        elif ctype == "BUTTONS":
            buttons = component.get("buttons") or []

    return {"header_type": header_type, "body": body, "footer": footer, "buttons": buttons}


def _render_meta_text(text: Optional[str], variables: Dict[str, str]) -> Optional[str]:
    if not text:
        return text
    def _sub(match: "re.Match") -> str:
        return str(variables.get(match.group(1), match.group(0)))
    return _META_VARIABLE_PATTERN.sub(_sub, text)


class WhatsAppTemplateService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = WhatsAppTemplateRepository(session)

    async def get_last_synced_at(self) -> Optional[datetime]:
        """Operational visibility — when the last Meta sync actually ran,
        independent of whether it changed any row (a sync that finds
        nothing new still updates this)."""
        result = await self.session.execute(
            select(EmailSyncState).where(EmailSyncState.sync_name == _SYNC_NAME)
        )
        state = result.scalar_one_or_none()
        return state.last_synced_at if state else None

    async def _set_last_synced_at(self, when: datetime) -> None:
        result = await self.session.execute(
            select(EmailSyncState).where(EmailSyncState.sync_name == _SYNC_NAME)
        )
        state = result.scalar_one_or_none()
        if state is None:
            state = EmailSyncState(id=uuid4(), sync_name=_SYNC_NAME, last_synced_at=when)
            self.session.add(state)
        else:
            state.last_synced_at = when
        await self.session.commit()

    async def list_templates(
        self, status: Optional[str] = None, language: Optional[str] = None,
    ) -> List[WhatsAppTemplateSchema]:
        templates = await self.repo.get_all(status=status, language=language)
        return [self._to_schema(t) for t in templates]

    async def get_template(self, template_id: UUID) -> WhatsAppTemplateSchema:
        template = await self.repo.get(template_id)
        if not template:
            raise WhatsAppTemplateNotFoundError(f"WhatsApp template {template_id} not found")
        return self._to_schema(template)

    async def get_by_name_and_language(
        self, template_name: str, language: str,
    ) -> Optional[WhatsAppTemplateSchema]:
        """Feature 5's send-time lookup — returns None (not an exception) so
        callers can decide the right HTTP status for "not found"."""
        template = await self.repo.get_by_name_and_language(template_name, language)
        return self._to_schema(template) if template else None

    async def preview(self, template_id: UUID, variables: Dict[str, str]) -> WhatsAppTemplatePreviewResponse:
        """Feature 6 — render body/header/footer with Meta's {{1}}/{{2}}
        placeholders replaced. Header is only rendered when it's a TEXT
        header (media headers have no template text to substitute)."""
        template = await self.repo.get(template_id)
        if not template:
            raise WhatsAppTemplateNotFoundError(f"WhatsApp template {template_id} not found")

        header_text = None
        return WhatsAppTemplatePreviewResponse(
            header=header_text,
            body=_render_meta_text(template.body, variables) or "",
            footer=_render_meta_text(template.footer, variables),
        )

    async def sync_from_meta(self) -> WhatsAppTemplateSyncResultSchema:
        """Feature 2 — pull every template Meta has for this WABA (any
        status; approval state changes over time, e.g. PENDING ->
        APPROVED, so non-approved templates must be tracked too, not
        skipped), upsert keyed on provider_template_id (dedupe — "Do not
        duplicate existing templates"), and report a summary.

        Only WhatsAppTemplateService writes to this table — this method is
        the entire write path (Feature 8).
        """
        provider = MetaProvider({})
        try:
            remote_templates = await provider.list_templates()
        except Exception as exc:
            raise MetaSyncError(f"Meta template list failed: {exc}") from exc

        scanned = created = updated = unchanged = 0

        for remote in remote_templates:
            scanned += 1
            provider_template_id = str(remote.get("id") or "")
            if not provider_template_id:
                logger.warning("Meta template sync: skipping entry with no id: %s", remote)
                continue

            parsed = _parse_components(remote.get("components") or [])
            variables = _extract_meta_variables(parsed["body"])

            existing = await self.repo.get_by_provider_template_id(provider_template_id)
            if existing is None:
                new_template = WhatsAppTemplate(
                    id=uuid4(),
                    provider_template_id=provider_template_id,
                    template_name=remote.get("name") or "",
                    language=remote.get("language") or "",
                    category=remote.get("category"),
                    status=remote.get("status") or "UNKNOWN",
                    header_type=parsed["header_type"],
                    body=parsed["body"],
                    footer=parsed["footer"],
                    buttons=parsed["buttons"],
                    variables=variables,
                )
                await self.repo.create(new_template)
                created += 1
                continue

            changed = (
                existing.status != (remote.get("status") or "UNKNOWN")
                or existing.template_name != (remote.get("name") or "")
                or existing.language != (remote.get("language") or "")
                or existing.category != remote.get("category")
                or existing.header_type != parsed["header_type"]
                or existing.body != parsed["body"]
                or existing.footer != parsed["footer"]
                or (existing.buttons or []) != parsed["buttons"]
                or (existing.variables or []) != variables
            )
            if not changed:
                unchanged += 1
                continue

            existing.status = remote.get("status") or "UNKNOWN"
            existing.template_name = remote.get("name") or ""
            existing.language = remote.get("language") or ""
            existing.category = remote.get("category")
            existing.header_type = parsed["header_type"]
            existing.body = parsed["body"]
            existing.footer = parsed["footer"]
            existing.buttons = parsed["buttons"]
            existing.variables = variables
            await self.repo.update(existing)
            updated += 1

        synced_at = datetime.utcnow()
        await self._set_last_synced_at(synced_at)

        return WhatsAppTemplateSyncResultSchema(
            scanned=scanned, created=created, updated=updated, unchanged=unchanged,
            last_synced_at=synced_at,
        )

    def _to_schema(self, template: WhatsAppTemplate) -> WhatsAppTemplateSchema:
        return WhatsAppTemplateSchema(
            id=str(template.id),
            provider_template_id=template.provider_template_id,
            template_name=template.template_name,
            language=template.language,
            category=template.category,
            status=template.status,
            header_type=template.header_type,
            body=template.body,
            footer=template.footer,
            buttons=template.buttons or [],
            variables=template.variables or [],
            created_at=template.created_at,
            updated_at=template.updated_at,
        )

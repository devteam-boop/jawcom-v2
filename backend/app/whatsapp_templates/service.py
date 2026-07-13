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
    WhatsAppTemplateCreateSchema,
    WhatsAppTemplateVersionsResponse,
    WhatsAppTemplatePreviewResponse,
)
from .exceptions import (
    WhatsAppTemplateNotFoundError,
    WhatsAppTemplateInvalidStateError,
    MetaSyncError,
    MetaSubmissionError,
)

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
    flat header_type/header_text/body/footer/buttons columns."""
    header_type = None
    header_text = None
    body = ""
    footer = None
    buttons: List[Dict[str, Any]] = []

    for component in components or []:
        ctype = (component.get("type") or "").upper()
        if ctype == "HEADER":
            header_type = component.get("format")
            if header_type == "TEXT":
                header_text = component.get("text")
        elif ctype == "BODY":
            body = component.get("text") or ""
        elif ctype == "FOOTER":
            footer = component.get("text")
        elif ctype == "BUTTONS":
            buttons = component.get("buttons") or []

    return {
        "header_type": header_type, "header_text": header_text,
        "body": body, "footer": footer, "buttons": buttons,
    }


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

    async def get_last_sync_error(self) -> Optional[str]:
        """Phase 7 "Sync Status" — the error from the last sync attempt that
        failed, if any. Cleared (set to None) by a subsequent successful
        sync — see sync_from_meta()."""
        result = await self.session.execute(
            select(EmailSyncState).where(EmailSyncState.sync_name == _SYNC_NAME)
        )
        state = result.scalar_one_or_none()
        return state.last_error if state else None

    async def _set_sync_state(self, when: Optional[datetime], error: Optional[str]) -> None:
        result = await self.session.execute(
            select(EmailSyncState).where(EmailSyncState.sync_name == _SYNC_NAME)
        )
        state = result.scalar_one_or_none()
        if state is None:
            state = EmailSyncState(id=uuid4(), sync_name=_SYNC_NAME, last_synced_at=when, last_error=error)
            self.session.add(state)
        else:
            if when is not None:
                state.last_synced_at = when
            state.last_error = error
        await self.session.commit()

    async def list_templates(
        self, status: Optional[str] = None, language: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[WhatsAppTemplateSchema]:
        """Admin/full listing (Phase 1 backend) — every status, every
        version. Not the client-facing "latest approved only" view (see
        list_latest_approved)."""
        templates = await self.repo.get_all(status=status, language=language, search=search)
        return [self._to_schema(t) for t in templates]

    async def list_latest_approved(self, language: Optional[str] = None) -> List[WhatsAppTemplateSchema]:
        """Phase 6 — one row per family: its highest-version APPROVED row,
        or nothing if that family has no approved version at all. Backs
        TemplateService.list_templates(channel="whatsapp") -> GET
        /api/templates and GET /api/messages/templates (JAWIS)."""
        templates = await self.repo.get_latest_approved_per_family(language=language)
        return [self._to_schema(t) for t in templates]

    async def get_template(self, template_id: UUID) -> WhatsAppTemplateSchema:
        template = await self.repo.get(template_id)
        if not template:
            raise WhatsAppTemplateNotFoundError(f"WhatsApp template {template_id} not found")
        return self._to_schema(template)

    async def get_family_versions(self, family_id: UUID) -> WhatsAppTemplateVersionsResponse:
        """Phase 5 — full version history for one template family, newest first."""
        versions = await self.repo.get_versions_by_family(family_id)
        if not versions:
            raise WhatsAppTemplateNotFoundError(f"No template family {family_id} found")
        return WhatsAppTemplateVersionsResponse(
            family_id=str(family_id),
            versions=[self._to_schema(t) for t in versions],
        )

    async def resolve_latest_approved_by_name(
        self, template_name: str, language: str,
    ) -> Optional[WhatsAppTemplateSchema]:
        """Phase 5's manual-send resolution point — returns None (not an
        exception) so the caller can surface a clear, explicit "no approved
        version" error rather than silently falling back to an unapproved
        one (see message_routes.py send_whatsapp())."""
        template = await self.repo.get_latest_approved_by_name(template_name, language)
        return self._to_schema(template) if template else None

    async def create_draft(self, data: WhatsAppTemplateCreateSchema) -> WhatsAppTemplateSchema:
        """Phase 2 — local-only row, status=DRAFT, no Meta call. If a
        family with this exact (template_name, language) already exists
        (any status), this becomes that family's next version instead of a
        new family — this is the "edit and resubmit creates a new version"
        mechanism from Phase 5: there is no separate update/PATCH endpoint,
        every save is a new version row."""
        variables = _extract_meta_variables(data.body)

        existing_latest = await self.repo.get_latest_version_by_name(data.template_name, data.language)
        if existing_latest is not None:
            family_id = existing_latest.family_id
            version = existing_latest.version + 1
        else:
            # Deliberately a SEPARATE uuid4(), not the new row's own id: if
            # family_id ever equalled a row's id, TemplateService.get_template()
            # would match that row directly (step 2) before ever reaching the
            # family_id fallback (step 3), making "resolve to latest approved
            # via family_id" unreachable for a family's founding version.
            family_id = uuid4()
            version = 1

        template = WhatsAppTemplate(
            id=uuid4(),
            family_id=family_id,
            version=version,
            provider_template_id=None,
            template_name=data.template_name,
            language=data.language,
            category=data.category,
            status="DRAFT",
            header_type=data.header_type,
            header_text=data.header_text if data.header_type == "TEXT" else None,
            header_media_url=data.header_media_url if data.header_type not in (None, "TEXT") else None,
            body=data.body,
            footer=data.footer,
            buttons=data.buttons,
            variables=variables,
            examples=data.examples,
        )
        created = await self.repo.create(template)
        return self._to_schema(created)

    async def submit_to_meta(self, template_id: UUID) -> WhatsAppTemplateSchema:
        """Phase 3 — "Submit to Meta" action on a DRAFT template.

        Never fabricates approval: a successful Meta response only ever
        moves status DRAFT -> PENDING (Meta's own genuine acknowledgement
        that review has started) and stores the real provider_template_id
        Meta returned. A Meta rejection/error raises MetaSubmissionError
        with Meta's real message, and the row is left untouched (still
        DRAFT) — the caller (route) surfaces this verbatim rather than
        swallowing it.
        """
        template = await self.repo.get(template_id)
        if not template:
            raise WhatsAppTemplateNotFoundError(f"WhatsApp template {template_id} not found")
        if template.status != "DRAFT":
            raise WhatsAppTemplateInvalidStateError(
                f"Template {template_id} is '{template.status}', not DRAFT — only a DRAFT can be submitted "
                "(create a new version via create_draft() to edit and resubmit)"
            )
        if template.header_type not in (None, "TEXT"):
            raise WhatsAppTemplateInvalidStateError(
                f"Header type '{template.header_type}' requires a Meta media handle, which this build does not "
                "yet upload (Phase 2's header_media_url is a schema stub only) — cannot submit this template"
            )

        components: List[Dict[str, Any]] = []
        if template.header_type == "TEXT" and template.header_text:
            components.append({"type": "HEADER", "format": "TEXT", "text": template.header_text})

        body_component: Dict[str, Any] = {"type": "BODY", "text": template.body}
        if template.variables:
            body_component["example"] = {"body_text": [template.examples or []]}
        components.append(body_component)

        if template.footer:
            components.append({"type": "FOOTER", "text": template.footer})
        if template.buttons:
            components.append({"type": "BUTTONS", "buttons": template.buttons})

        provider = MetaProvider({})
        try:
            response = await provider.create_template(
                name=template.template_name,
                category=template.category or "UTILITY",
                language=template.language,
                components=components,
            )
        except Exception as exc:
            # Real Meta error (malformed/restricted/expired token/permission)
            # — status stays DRAFT (never set to PENDING on a failed call),
            # but the real error is persisted onto the row so it's visible
            # in the Submitted/In Review panel without needing to re-read
            # server logs, not just surfaced transiently to the caller.
            template.rejection_reason = str(exc)
            await self.repo.update(template)
            raise MetaSubmissionError(str(exc)) from exc

        provider_template_id = str(response.get("id") or "")
        if not provider_template_id:
            error = f"Meta accepted the submission but returned no template id: {response}"
            template.rejection_reason = error
            await self.repo.update(template)
            raise MetaSubmissionError(error)

        logger.info(
            "WhatsAppTemplateService.submit_to_meta: template=%s provider_template_id=%s",
            template.template_name, provider_template_id,
        )

        template.provider_template_id = provider_template_id
        # Meta's create response includes its own initial status (almost
        # always "PENDING") — used verbatim rather than hardcoded, but never
        # trusted to already say APPROVED (see class docstring: approval is
        # only ever learned via sync_from_meta()).
        template.status = response.get("status") or "PENDING"
        if template.status == "APPROVED":
            logger.warning(
                "Meta's create-template response for %s claimed APPROVED at submission time — "
                "storing PENDING instead; approval is only trusted via a subsequent sync",
                template.template_name,
            )
            template.status = "PENDING"
        # Clears any rejection_reason left over from a previous failed
        # submit attempt on this same DRAFT row — this is a fresh, genuine
        # Meta acceptance, so a stale error from an earlier try must not
        # keep showing next to the new PENDING status.
        template.rejection_reason = None
        template.last_synced_at = datetime.utcnow()
        await self.repo.update(template)
        return self._to_schema(template)

    async def preview(self, template_id: UUID, variables: Dict[str, str]) -> WhatsAppTemplatePreviewResponse:
        """Feature 6 — render body/header/footer with Meta's {{1}}/{{2}}
        placeholders replaced. Header is only rendered when it's a TEXT
        header (media headers have no template text to substitute)."""
        template = await self.repo.get(template_id)
        if not template:
            raise WhatsAppTemplateNotFoundError(f"WhatsApp template {template_id} not found")

        header_text = template.header_text if template.header_type == "TEXT" else None
        return WhatsAppTemplatePreviewResponse(
            header=_render_meta_text(header_text, variables),
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
            error = f"Meta template list failed: {exc}"
            await self._set_sync_state(when=None, error=error)
            raise MetaSyncError(error) from exc

        # One timestamp for the whole pass — every row this sync scans is
        # "confirmed against Meta as of" the same moment, whether or not its
        # content actually changed.
        synced_at = datetime.utcnow()
        scanned = created = updated = unchanged = 0

        for remote in remote_templates:
            scanned += 1
            provider_template_id = str(remote.get("id") or "")
            if not provider_template_id:
                logger.warning("Meta template sync: skipping entry with no id: %s", remote)
                continue

            parsed = _parse_components(remote.get("components") or [])
            variables = _extract_meta_variables(parsed["body"])
            quality_rating = ((remote.get("quality_score") or {}).get("score")) or None
            rejection_reason = remote.get("rejected_reason") or None
            if rejection_reason == "NONE":  # Meta's literal placeholder when not rejected
                rejection_reason = None

            existing = await self.repo.get_by_provider_template_id(provider_template_id)
            if existing is None:
                # family_id is a separate uuid4(), NOT the row's own id — see
                # create_draft()'s comment on why the two must never be equal.
                new_template = WhatsAppTemplate(
                    id=uuid4(),
                    family_id=uuid4(),  # a template Meta already has that JawCom never drafted: its own new family
                    version=1,
                    provider_template_id=provider_template_id,
                    template_name=remote.get("name") or "",
                    language=remote.get("language") or "",
                    category=remote.get("category"),
                    status=remote.get("status") or "UNKNOWN",
                    header_type=parsed["header_type"],
                    header_text=parsed["header_text"],
                    body=parsed["body"],
                    footer=parsed["footer"],
                    buttons=parsed["buttons"],
                    variables=variables,
                    quality_rating=quality_rating,
                    rejection_reason=rejection_reason,
                    last_synced_at=synced_at,
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
                or existing.header_text != parsed["header_text"]
                or existing.body != parsed["body"]
                or existing.footer != parsed["footer"]
                or (existing.buttons or []) != parsed["buttons"]
                or (existing.variables or []) != variables
                or existing.quality_rating != quality_rating
                or existing.rejection_reason != rejection_reason
            )
            if not changed:
                # Content is identical, but this row was still just
                # reconfirmed against Meta — stamp last_synced_at so its
                # freshness marker doesn't go stale just because nothing else
                # changed.
                existing.last_synced_at = synced_at
                await self.repo.update(existing)
                unchanged += 1
                continue

            existing.status = remote.get("status") or "UNKNOWN"
            existing.template_name = remote.get("name") or ""
            existing.language = remote.get("language") or ""
            existing.category = remote.get("category")
            existing.header_type = parsed["header_type"]
            existing.header_text = parsed["header_text"]
            existing.body = parsed["body"]
            existing.footer = parsed["footer"]
            existing.buttons = parsed["buttons"]
            existing.variables = variables
            existing.quality_rating = quality_rating
            existing.rejection_reason = rejection_reason
            existing.last_synced_at = synced_at
            await self.repo.update(existing)
            updated += 1

        await self._set_sync_state(when=synced_at, error=None)

        return WhatsAppTemplateSyncResultSchema(
            scanned=scanned, created=created, updated=updated, unchanged=unchanged,
            last_synced_at=synced_at,
        )

    async def update_status_from_webhook(
        self,
        meta_template_id: str,
        status: Optional[str] = None,
        rejection_reason: Optional[str] = None,
        quality_rating: Optional[str] = None,
        category: Optional[str] = None,
        language: Optional[str] = None,
    ) -> Optional[WhatsAppTemplateSchema]:
        """Part 3 — applies a single message_template_status_update webhook
        event to the matching row, keyed by meta_template_id (this table's
        provider_template_id — the same dedupe key sync_from_meta() upserts
        on). Only touches fields the webhook payload actually supplied
        (Meta's real payload for this event does not include every field
        sync_from_meta() tracks, e.g. category/quality_rating are usually
        absent) — never overwrites a known value with None just because the
        webhook body didn't carry it.

        Returns None (does not raise) when no row matches yet — this can
        legitimately happen if Meta's push arrives before this template has
        ever been synced/created locally; the caller (webhook route) must
        still return 200 to Meta regardless.
        """
        template = await self.repo.get_by_provider_template_id(meta_template_id)
        if template is None:
            return None

        if status is not None:
            template.status = status
        if rejection_reason is not None:
            template.rejection_reason = rejection_reason
        if quality_rating is not None:
            template.quality_rating = quality_rating
        if category is not None:
            template.category = category
        if language is not None:
            template.language = language
        template.last_synced_at = datetime.utcnow()

        await self.repo.update(template)
        return self._to_schema(template)

    def _to_schema(self, template: WhatsAppTemplate) -> WhatsAppTemplateSchema:
        return WhatsAppTemplateSchema(
            id=str(template.id),
            provider_template_id=template.provider_template_id,
            template_name=template.template_name,
            language=template.language,
            category=template.category,
            status=template.status,
            header_type=template.header_type,
            header_text=template.header_text,
            header_media_url=template.header_media_url,
            body=template.body,
            footer=template.footer,
            buttons=template.buttons or [],
            variables=template.variables or [],
            examples=template.examples or [],
            family_id=str(template.family_id),
            version=template.version,
            quality_rating=template.quality_rating,
            rejection_reason=template.rejection_reason,
            last_synced_at=template.last_synced_at,
            usage_count=template.usage_count,
            last_used_at=template.last_used_at,
            created_at=template.created_at,
            updated_at=template.updated_at,
        )

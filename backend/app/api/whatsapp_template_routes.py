"""WhatsApp Template Management — admin actions (create, submit-to-Meta,
sync, preview, version history).

Client-facing listing/detail (Phases 3/4/6 of the original build) are
deliberately NOT duplicated here — they're exposed by extending the
existing GET /api/templates and GET /api/templates/{id} (see
app/api/template_routes.py) so JAWIS and the frontend keep using one
template listing endpoint regardless of channel, always restricted to the
latest APPROVED version per family. This router carries everything that has
no generic-table equivalent: the full admin listing (any status/version,
for the Phase 1 UI), creating a local DRAFT, submitting a DRAFT to Meta,
triggering a sync, rendering a preview, and reading one family's version
history.

Unauthenticated, matching every other Template Engine admin route in
template_routes.py today (this is an admin/operator surface, not a
JAWIS-facing endpoint — JAWIS never talks to Meta directly, per this
feature's architecture rules, so it has no reason to call this router).
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session
from app.whatsapp_templates.schemas import (
    WhatsAppTemplateSchema,
    WhatsAppTemplateCreateSchema,
    WhatsAppTemplateVersionsResponse,
    WhatsAppTemplateSyncResultSchema,
    WhatsAppTemplateSyncStatusSchema,
    WhatsAppTemplatePreviewRequest,
    WhatsAppTemplatePreviewResponse,
)
from app.whatsapp_templates.service import WhatsAppTemplateService
from app.whatsapp_templates.exceptions import (
    WhatsAppTemplateNotFoundError,
    WhatsAppTemplateInvalidStateError,
    MetaSyncError,
    MetaSubmissionError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/whatsapp-templates", tags=["WhatsApp Templates"])


@router.get(
    "",
    response_model=List[WhatsAppTemplateSchema],
    summary="Admin listing — every status and version (Phase 1 UI data source)",
    description=(
        "Unlike GET /api/templates?channel=whatsapp (client-facing, latest-"
        "approved-only), this returns every whatsapp_templates row matching "
        "the filters, including Draft/Pending/Rejected/older versions — "
        "backs the Templates management screen, not the send/JAWIS path."
    ),
)
async def list_whatsapp_templates(
    status: Optional[str] = None,
    language: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
):
    service = WhatsAppTemplateService(db)
    return await service.list_templates(status=status, language=language, search=search)


@router.post(
    "",
    response_model=WhatsAppTemplateSchema,
    status_code=201,
    summary="Create a local WhatsApp template DRAFT (no Meta call)",
    description=(
        "Local-only row, status=DRAFT. If a family with this exact "
        "(template_name, language) already exists, this becomes its next "
        "version instead of a new family — this is how 'edit and resubmit' "
        "works (Phase 5): there is no separate update endpoint."
    ),
)
async def create_whatsapp_template_draft(
    data: WhatsAppTemplateCreateSchema,
    db: AsyncSession = Depends(get_db_session),
):
    service = WhatsAppTemplateService(db)
    return await service.create_draft(data)


@router.post(
    "/{template_id}/submit",
    response_model=WhatsAppTemplateSchema,
    summary="Submit a DRAFT template to Meta for review",
    description=(
        "Calls Meta's real template-creation API. On genuine Meta "
        "acceptance, stores the returned Meta Template ID and sets "
        "status=PENDING. On a Meta rejection/error, raises with Meta's "
        "real message and leaves the row untouched (still DRAFT) — never "
        "fabricates or assumes approval; APPROVED is only ever learned via "
        "a subsequent sync."
    ),
)
async def submit_whatsapp_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    service = WhatsAppTemplateService(db)
    try:
        return await service.submit_to_meta(template_id)
    except WhatsAppTemplateNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except WhatsAppTemplateInvalidStateError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except MetaSubmissionError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get(
    "/{template_id}/versions",
    response_model=WhatsAppTemplateVersionsResponse,
    summary="Full version history for one template family (Phase 5)",
    description="template_id may be any version's row id — resolves to its family.",
)
async def get_whatsapp_template_versions(
    template_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    service = WhatsAppTemplateService(db)
    try:
        template = await service.get_template(template_id)
    except WhatsAppTemplateNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return await service.get_family_versions(UUID(template.family_id))


@router.post(
    "/sync",
    response_model=WhatsAppTemplateSyncResultSchema,
    summary="Sync WhatsApp templates from Meta Cloud API ('Sync Now')",
    description=(
        "Fetches every message template Meta has for the configured WABA, "
        "upserts by provider_template_id (no duplicates), and updates "
        "status/quality_rating/rejection_reason/category/language when "
        "Meta's copy has changed. No manual DB edits should ever be needed "
        "to reflect Meta's state."
    ),
)
async def sync_whatsapp_templates(db: AsyncSession = Depends(get_db_session)):
    service = WhatsAppTemplateService(db)
    try:
        return await service.sync_from_meta()
    except MetaSyncError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get(
    "/sync-status",
    response_model=WhatsAppTemplateSyncStatusSchema,
    summary="When the last Meta template sync ran, and whether it failed (operational visibility)",
)
async def whatsapp_templates_sync_status(db: AsyncSession = Depends(get_db_session)):
    service = WhatsAppTemplateService(db)
    return WhatsAppTemplateSyncStatusSchema(
        last_synced_at=await service.get_last_synced_at(),
        last_error=await service.get_last_sync_error(),
    )


@router.post(
    "/{template_id}/preview",
    response_model=WhatsAppTemplatePreviewResponse,
    summary="Render a WhatsApp template preview with variables substituted",
)
async def preview_whatsapp_template(
    template_id: UUID,
    request: WhatsAppTemplatePreviewRequest,
    db: AsyncSession = Depends(get_db_session),
):
    service = WhatsAppTemplateService(db)
    try:
        return await service.preview(template_id, request.variables)
    except WhatsAppTemplateNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

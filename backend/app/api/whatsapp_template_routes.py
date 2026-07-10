"""WhatsApp Template Management — sync + preview (Phase 1, Features 2/6).

Listing/detail (Features 3/4) are deliberately NOT duplicated here — they're
exposed by extending the existing GET /api/templates and
GET /api/templates/{id} (see app/api/template_routes.py) so JAWIS and the
frontend keep using one template listing endpoint regardless of channel.
This router only carries the two actions that have no generic-table
equivalent: triggering a Meta sync, and rendering a preview.

Unauthenticated, matching every other Template Engine admin route in
template_routes.py today (this is an admin/operator action, not a
JAWIS-facing endpoint — JAWIS never talks to Meta directly, per this
feature's architecture rules, so it has no reason to call this router).
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session
from app.whatsapp_templates.schemas import (
    WhatsAppTemplateSyncResultSchema,
    WhatsAppTemplateSyncStatusSchema,
    WhatsAppTemplatePreviewRequest,
    WhatsAppTemplatePreviewResponse,
)
from app.whatsapp_templates.service import WhatsAppTemplateService
from app.whatsapp_templates.exceptions import WhatsAppTemplateNotFoundError, MetaSyncError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/whatsapp-templates", tags=["WhatsApp Templates"])


@router.post(
    "/sync",
    response_model=WhatsAppTemplateSyncResultSchema,
    summary="Sync approved WhatsApp templates from Meta Cloud API",
    description=(
        "Fetches every message template Meta has for the configured WABA, "
        "upserts by provider_template_id (no duplicates), and updates "
        "status when Meta's copy has changed. This is the only way "
        "whatsapp_templates rows are ever created — there is no manual "
        "create/edit/delete for this table."
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
    summary="When the last Meta template sync ran (operational visibility)",
)
async def whatsapp_templates_sync_status(db: AsyncSession = Depends(get_db_session)):
    service = WhatsAppTemplateService(db)
    return WhatsAppTemplateSyncStatusSchema(last_synced_at=await service.get_last_synced_at())


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

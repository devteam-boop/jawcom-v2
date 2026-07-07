from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session
from app.templates.schemas import (
    TemplateSchema,
    TemplateCreateSchema,
    TemplateUpdateSchema,
    TemplateUsageSchema,
)
from app.templates.services import TemplateService
from app.templates.exceptions import (
    TemplateNotFoundError,
    TemplateValidationError,
    TemplateInUseError,
)

router = APIRouter(
    prefix="/api/templates",
    tags=["Templates"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=TemplateSchema, status_code=201,
             summary="Create a template",
             description="Creates a new communication template (email/sms/whatsapp/push).")
async def create_template(
    data: TemplateCreateSchema,
    db: AsyncSession = Depends(get_db_session),
):
    service = TemplateService(db)
    try:
        return await service.create_template(data)
    except TemplateValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[TemplateSchema],
            summary="List templates",
            description="Returns templates, optionally filtered by channel and/or status.")
async def list_templates(
    channel: Optional[str] = Query(None, description="Filter by channel (email|sms|whatsapp|push)"),
    status: Optional[str] = Query(None, description="Filter by status (draft|active|inactive)"),
    db: AsyncSession = Depends(get_db_session),
):
    service = TemplateService(db)
    return await service.list_templates(channel=channel, status=status)


@router.get("/{template_id}", response_model=TemplateSchema,
            summary="Get template by ID")
async def get_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    service = TemplateService(db)
    try:
        return await service.get_template(template_id)
    except TemplateNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{template_id}", response_model=TemplateSchema,
              summary="Update template",
              description="Updates one or more fields of a template.")
async def update_template(
    template_id: UUID,
    data: TemplateUpdateSchema,
    db: AsyncSession = Depends(get_db_session),
):
    service = TemplateService(db)
    try:
        return await service.update_template(template_id, data)
    except TemplateNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TemplateValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{template_id}", status_code=204,
               summary="Delete template",
               description="Deletes a template. Fails if it is referenced by a stage mapping or flow node.")
async def delete_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    service = TemplateService(db)
    try:
        deleted = await service.delete_template(template_id)
    except TemplateNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TemplateInUseError as e:
        raise HTTPException(status_code=409, detail=str(e))
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Template {template_id} not found")


@router.post("/{template_id}/duplicate", response_model=TemplateSchema, status_code=201,
             summary="Duplicate template",
             description="Creates a draft copy of an existing template.")
async def duplicate_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    service = TemplateService(db)
    try:
        return await service.duplicate_template(template_id)
    except TemplateNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{template_id}/archive", response_model=TemplateSchema,
             summary="Archive template",
             description="Sets the template status to inactive.")
async def archive_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    service = TemplateService(db)
    try:
        return await service.archive_template(template_id)
    except TemplateNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{template_id}/usage", response_model=TemplateUsageSchema,
            summary="Get template usage",
            description="Lists stage mappings and flow nodes currently referencing this template.")
async def get_template_usage(
    template_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    service = TemplateService(db)
    return await service.get_template_usage(template_id)

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session
from app.flow_definitions.schemas import (
    FlowVersionSchema,
    FlowVersionCreateSchema,
)
from app.services.flow_version_service import FlowVersionService

router = APIRouter(
    prefix="/api/flow-versions",
    tags=["Flow Versions"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=FlowVersionSchema, status_code=201,
             summary="Create a flow version",
             description="Creates a new version snapshot for a flow definition. "
                         "The version number is auto-incremented.")
async def create_flow_version(
    data: FlowVersionCreateSchema,
    db: AsyncSession = Depends(get_db_session),
):
    service = FlowVersionService(db)
    try:
        return await service.create(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[FlowVersionSchema],
            summary="List flow versions",
            description="Returns a paginated list of flow versions, optionally filtered by flow definition.")
async def list_flow_versions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    flow_definition_id: Optional[UUID] = Query(None, description="Filter by flow definition ID"),
    db: AsyncSession = Depends(get_db_session),
):
    service = FlowVersionService(db)
    return await service.list(skip=skip, limit=limit, flow_definition_id=flow_definition_id)


@router.get("/{version_id}", response_model=FlowVersionSchema,
            summary="Get flow version by ID",
            description="Returns a single flow version snapshot.")
async def get_flow_version(
    version_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    service = FlowVersionService(db)
    try:
        return await service.get(version_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{version_id}", status_code=204,
               summary="Delete flow version",
               description="Deletes a flow version snapshot.")
async def delete_flow_version(
    version_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    service = FlowVersionService(db)
    deleted = await service.delete(version_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"FlowVersion {version_id} not found")

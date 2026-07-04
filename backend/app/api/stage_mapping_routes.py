from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session
from app.stage_mapping.schemas import StageMappingSchema, StageMappingCreateSchema, StageMappingUpdateSchema
from app.services.stage_mapping_service import StageMappingService

router = APIRouter(
    prefix="/api/stage-mappings",
    tags=["Stage Mappings"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=StageMappingSchema, status_code=201,
             summary="Create a stage mapping",
             description="Maps a lead stage key to a journey action with optional template reference.")
async def create_stage_mapping(
    data: StageMappingCreateSchema,
    db: AsyncSession = Depends(get_db_session),
):
    service = StageMappingService(db)
    try:
        return await service.create(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[StageMappingSchema],
            summary="List stage mappings",
            description="Returns paginated stage mappings, optionally filtered by journey.")
async def list_stage_mappings(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    journey_id: Optional[UUID] = Query(None, description="Filter by journey ID"),
    db: AsyncSession = Depends(get_db_session),
):
    service = StageMappingService(db)
    return await service.list(skip=skip, limit=limit, journey_id=journey_id)


@router.get("/{mapping_id}", response_model=StageMappingSchema,
            summary="Get stage mapping by ID",
            description="Returns a single stage mapping.")
async def get_stage_mapping(
    mapping_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    service = StageMappingService(db)
    try:
        return await service.get(mapping_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{mapping_id}", response_model=StageMappingSchema,
              summary="Update stage mapping",
              description="Updates one or more fields of a stage mapping.")
async def update_stage_mapping(
    mapping_id: UUID,
    data: StageMappingUpdateSchema,
    db: AsyncSession = Depends(get_db_session),
):
    service = StageMappingService(db)
    try:
        return await service.update(mapping_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{mapping_id}", status_code=204,
               summary="Delete stage mapping",
               description="Deletes a stage mapping.")
async def delete_stage_mapping(
    mapping_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    service = StageMappingService(db)
    deleted = await service.delete(mapping_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"StageMapping {mapping_id} not found")

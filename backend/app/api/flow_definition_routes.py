from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session
from app.flow_definitions.schemas import (
    FlowDefinitionSchema,
    FlowDefinitionCreateSchema,
    FlowDefinitionUpdateSchema,
)
from app.services.flow_definition_service import FlowDefinitionService

router = APIRouter(
    prefix="/api/flow-definitions",
    tags=["Flow Definitions"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=FlowDefinitionSchema, status_code=201,
             summary="Create a flow definition",
             description="Creates a new flow definition with a JSON definition and starts at version 1.")
async def create_flow_definition(
    data: FlowDefinitionCreateSchema,
    db: AsyncSession = Depends(get_db_session),
):
    service = FlowDefinitionService(db)
    return await service.create(data)


@router.get("/", response_model=List[FlowDefinitionSchema],
            summary="List flow definitions",
            description="Returns a paginated list of flow definitions, optionally filtered by status.")
async def list_flow_definitions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status: Optional[str] = Query(None, description="Filter by status (draft, published, archived)"),
    db: AsyncSession = Depends(get_db_session),
):
    service = FlowDefinitionService(db)
    return await service.list(skip=skip, limit=limit, status=status)


@router.get("/{definition_id}", response_model=FlowDefinitionSchema,
            summary="Get flow definition by ID",
            description="Returns a single flow definition.")
async def get_flow_definition(
    definition_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    service = FlowDefinitionService(db)
    try:
        return await service.get(definition_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{definition_id}", response_model=FlowDefinitionSchema,
              summary="Update flow definition",
              description="Updates one or more fields of a flow definition.")
async def update_flow_definition(
    definition_id: UUID,
    data: FlowDefinitionUpdateSchema,
    db: AsyncSession = Depends(get_db_session),
):
    service = FlowDefinitionService(db)
    try:
        return await service.update(definition_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{definition_id}", status_code=204,
               summary="Delete flow definition",
               description="Deletes a flow definition and its associated versions and execution logs.")
async def delete_flow_definition(
    definition_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    service = FlowDefinitionService(db)
    deleted = await service.delete(definition_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"FlowDefinition {definition_id} not found")


@router.post("/{definition_id}/publish", response_model=FlowDefinitionSchema,
             summary="Publish flow definition",
             description="Sets the flow definition status to published.")
async def publish_flow_definition(
    definition_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    service = FlowDefinitionService(db)
    try:
        return await service.publish(definition_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{definition_id}/archive", response_model=FlowDefinitionSchema,
             summary="Archive flow definition",
             description="Archives a flow definition, removing it from active view.")
async def archive_flow_definition(
    definition_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    service = FlowDefinitionService(db)
    try:
        return await service.archive(definition_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session
from app.journeys.schemas import JourneySchema, JourneyCreateSchema, JourneyUpdateSchema
from app.services.journey_service import JourneyService
from app.repositories.stage_mapping_repository import StageMappingRepository
from app.models.flow_definition import FlowDefinition

router = APIRouter(
    prefix="/api/journeys",
    tags=["Journeys"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=JourneySchema, status_code=201,
             summary="Create a new journey",
             description="Creates a journey definition with trigger configuration.")
async def create_journey(
    data: JourneyCreateSchema,
    db: AsyncSession = Depends(get_db_session),
):
    service = JourneyService(db)
    return await service.create(data)


@router.get("/", response_model=List[JourneySchema],
            summary="List journeys",
            description="Returns a paginated list of journeys, optionally filtered by status.")
async def list_journeys(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status: Optional[str] = Query(None, description="Filter by status (draft, active, paused, archived)"),
    db: AsyncSession = Depends(get_db_session),
):
    service = JourneyService(db)
    return await service.list(skip=skip, limit=limit, status=status)


@router.get("/{journey_id}", response_model=JourneySchema,
            summary="Get journey by ID",
            description="Returns a single journey definition.")
async def get_journey(
    journey_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    service = JourneyService(db)
    try:
        return await service.get(journey_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{journey_id}", response_model=JourneySchema,
              summary="Update journey",
              description="Updates one or more fields of a journey.")
async def update_journey(
    journey_id: UUID,
    data: JourneyUpdateSchema,
    db: AsyncSession = Depends(get_db_session),
):
    service = JourneyService(db)
    try:
        return await service.update(journey_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{journey_id}", status_code=204,
               summary="Delete journey",
               description="Deletes a journey and its associated stage mappings and instances.")
async def delete_journey(
    journey_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    service = JourneyService(db)
    deleted = await service.delete(journey_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Journey {journey_id} not found")


@router.post("/{journey_id}/activate", response_model=JourneySchema,
             summary="Activate journey",
             description="Sets journey status to active, enabling it to start for matching leads.")
async def activate_journey(
    journey_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    service = JourneyService(db)
    try:
        return await service.activate(journey_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{journey_id}/pause", response_model=JourneySchema,
             summary="Pause journey",
             description="Pauses a journey, preventing new instances from starting.")
async def pause_journey(
    journey_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    service = JourneyService(db)
    try:
        return await service.pause(journey_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{journey_id}/archive", response_model=JourneySchema,
             summary="Archive journey",
             description="Archives a journey, removing it from active view.")
async def archive_journey(
    journey_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    service = JourneyService(db)
    try:
        return await service.archive(journey_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── Publish ─────────────────────────────────────────────────────────


class PublishResult(BaseModel):
    success: bool
    message: str
    errors: Optional[List[str]] = None


@router.post("/{journey_id}/publish", response_model=PublishResult,
             summary="Publish journey (validate + publish flow + activate)",
             description="Validates that the journey has a trigger stage, a flow, and a trigger node, "
                         "then publishes the flow definition and activates the journey.")
async def publish_journey(
    journey_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    service = JourneyService(db)
    try:
        journey = await service.get(journey_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Journey not found")

    errors = []

    # 1. Check trigger stage
    mapping_repo = StageMappingRepository(db)
    mappings = await mapping_repo.get_by_journey(journey_id)
    if not mappings:
        errors.append("Trigger Stage is not configured. Select a lead stage first.")

    # 2. Check flow definition exists
    if not journey.flow_definition_id:
        errors.append("Flow Definition is not created. Build a flow first.")

    # 3. Check flow has a trigger node
    if journey.flow_definition_id:
        stmt = select(FlowDefinition).where(FlowDefinition.id == UUID(journey.flow_definition_id))
        result = await db.execute(stmt)
        flow_def = result.scalar_one_or_none()
        if flow_def:
            nodes = (flow_def.definition or {}).get("nodes") or []
            has_trigger = any(
                isinstance(n, dict) and n.get("type") == "trigger"
                for n in nodes
            )
            if not has_trigger:
                errors.append("Flow must contain at least one Trigger node.")

    if errors:
        return PublishResult(
            success=False,
            message="Validation failed. Fix the issues below and try again.",
            errors=errors,
        )

    # Publish the flow definition
    from app.services.flow_definition_service import FlowDefinitionService
    flow_def_service = FlowDefinitionService(db)
    await flow_def_service.publish(UUID(journey.flow_definition_id))
    await flow_def_service.get(UUID(journey.flow_definition_id))

    # Activate the journey
    await service.activate(journey_id)

    return PublishResult(
        success=True,
        message="Journey published successfully. It is now active and ready to receive leads.",
    )

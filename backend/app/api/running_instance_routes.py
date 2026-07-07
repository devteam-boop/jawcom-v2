from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session
from app.runtime.schemas import RunningInstanceSchema, RunningInstanceCreateSchema, RunningInstanceUpdateSchema
from app.services.running_instance_service import RunningInstanceService
from app.services.retry_service import RetryService
from app.database.session import async_session_maker

router = APIRouter(
    prefix="/api/running-instances",
    tags=["Running Instances"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=RunningInstanceSchema, status_code=201,
             summary="Start a journey instance for a lead",
             description="Creates a new running journey instance, linking a lead to a journey. "
                         "The lead_id references the existing leads table.")
async def create_running_instance(
    data: RunningInstanceCreateSchema,
    db: AsyncSession = Depends(get_db_session),
):
    service = RunningInstanceService(db)
    try:
        return await service.create(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[RunningInstanceSchema],
            summary="List running instances",
            description="Returns paginated running instances, optionally filtered by journey, status, or lead.")
async def list_running_instances(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    journey_id: Optional[UUID] = Query(None, description="Filter by journey ID"),
    status: Optional[str] = Query(None, description="Filter by status (running, completed, failed, waiting)"),
    lead_id: Optional[int] = Query(None, description="Filter by lead ID"),
    db: AsyncSession = Depends(get_db_session),
):
    service = RunningInstanceService(db)
    return await service.list(
        skip=skip, limit=limit, journey_id=journey_id,
        status=status, lead_id=lead_id,
    )


@router.get("/{instance_id}", response_model=RunningInstanceSchema,
            summary="Get running instance by ID",
            description="Returns a single running journey instance.")
async def get_running_instance(
    instance_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    service = RunningInstanceService(db)
    try:
        return await service.get(instance_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{instance_id}", response_model=RunningInstanceSchema,
              summary="Update running instance",
              description="Updates one or more fields of a running instance, e.g. current stage or status.")
async def update_running_instance(
    instance_id: UUID,
    data: RunningInstanceUpdateSchema,
    db: AsyncSession = Depends(get_db_session),
):
    service = RunningInstanceService(db)
    try:
        return await service.update(instance_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{instance_id}", status_code=204,
               summary="Delete running instance",
               description="Deletes a running journey instance.")
async def delete_running_instance(
    instance_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    service = RunningInstanceService(db)
    deleted = await service.delete(instance_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"RunningInstance {instance_id} not found")


@router.post("/{instance_id}/complete", response_model=RunningInstanceSchema,
             summary="Complete a running instance",
             description="Marks the instance as completed and sets the completion timestamp.")
async def complete_running_instance(
    instance_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    service = RunningInstanceService(db)
    try:
        return await service.complete(instance_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{instance_id}/fail", response_model=RunningInstanceSchema,
             summary="Fail a running instance",
             description="Marks the instance as failed and sets the completion timestamp.")
async def fail_running_instance(
    instance_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    service = RunningInstanceService(db)
    try:
        return await service.fail(instance_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{instance_id}/retry", response_model=dict,
             summary="Retry a failed instance",
             description="Retries a failed journey instance. Supports two modes: "
                         "'node' (default) re-executes the failed node, "
                         "'journey' restarts the entire journey from the trigger node.")
async def retry_running_instance(
    instance_id: UUID,
    mode: str = Query("node", regex="^(node|journey)$"),
):
    retry_service = RetryService(async_session_maker)
    try:
        if mode == "journey":
            success = await retry_service.retry_journey(instance_id)
        else:
            success = await retry_service.retry_node(instance_id)
        return {"success": success, "mode": mode, "instance_id": str(instance_id)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{instance_id}/resume", response_model=dict,
             summary="Resume a waiting instance",
             description="Resumes a waiting journey instance. The wait/delay node "
                         "is skipped and traversal continues to the downstream nodes.")
async def resume_running_instance(
    instance_id: UUID,
):
    from app.execution.engine import ExecutionEngine

    engine = ExecutionEngine(async_session_maker)
    try:
        success = await engine.resume_instance(instance_id)
        return {"success": success, "instance_id": str(instance_id)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

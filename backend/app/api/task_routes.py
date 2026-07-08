from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session
from app.database.session import async_session_maker
from app.services.task_service import TaskService
from app.services.running_instance_service import RunningInstanceService
from app.services.communication_event_service import CommunicationEventService

router = APIRouter(
    prefix="/api/tasks",
    tags=["Tasks"],
    responses={404: {"description": "Not found"}},
)


@router.get("/{instance_id}", response_model=list)
async def list_tasks(
    instance_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    instance_service = RunningInstanceService(db)
    service = TaskService(instance_service)
    return await service.list_tasks(instance_id)


@router.post("/{instance_id}/{task_id}/complete", response_model=dict)
async def complete_task(
    instance_id: UUID,
    task_id: str,
    completed_by: str = Query("system", description="Who completed this task"),
    db: AsyncSession = Depends(get_db_session),
):
    instance_service = RunningInstanceService(db)
    event_service = CommunicationEventService(db)
    service = TaskService(instance_service, event_service)
    try:
        result = await service.complete_task(instance_id, task_id, completed_by)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    from app.execution.engine import ExecutionEngine
    engine = ExecutionEngine(async_session_maker)
    success = await engine.resume_instance(instance_id)
    return {"task": result, "resumed": success}


@router.post("/{instance_id}/{task_id}/reject", response_model=dict)
async def reject_task(
    instance_id: UUID,
    task_id: str,
    completed_by: str = Query("system", description="Who rejected this task"),
    db: AsyncSession = Depends(get_db_session),
):
    instance_service = RunningInstanceService(db)
    service = TaskService(instance_service)
    try:
        result = await service.reject_task(instance_id, task_id, completed_by)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    from app.execution.engine import ExecutionEngine
    engine = ExecutionEngine(async_session_maker)
    success = await engine.resume_instance(instance_id)
    return {"task": result, "resumed": success}

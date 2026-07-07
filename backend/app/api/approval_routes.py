from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session
from app.database.session import async_session_maker
from app.services.approval_service import ApprovalService
from app.services.running_instance_service import RunningInstanceService

router = APIRouter(
    prefix="/api/approvals",
    tags=["Approvals"],
    responses={404: {"description": "Not found"}},
)


@router.get("/{instance_id}", response_model=list)
async def list_approvals(
    instance_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    instance_service = RunningInstanceService(db)
    service = ApprovalService(instance_service)
    return await service.list_approvals(instance_id)


@router.post("/{instance_id}/{approval_id}/approve", response_model=dict)
async def approve_approval(
    instance_id: UUID,
    approval_id: str,
    resolved_by: str = Query("system", description="Who resolved this approval"),
    db: AsyncSession = Depends(get_db_session),
):
    instance_service = RunningInstanceService(db)
    service = ApprovalService(instance_service)
    try:
        result = await service.approve(instance_id, approval_id, resolved_by)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    from app.execution.engine import ExecutionEngine
    engine = ExecutionEngine(async_session_maker)
    success = await engine.resume_instance(instance_id)
    return {"approval": result, "resumed": success}


@router.post("/{instance_id}/{approval_id}/reject", response_model=dict)
async def reject_approval(
    instance_id: UUID,
    approval_id: str,
    resolved_by: str = Query("system", description="Who resolved this approval"),
    db: AsyncSession = Depends(get_db_session),
):
    instance_service = RunningInstanceService(db)
    service = ApprovalService(instance_service)
    try:
        result = await service.reject(instance_id, approval_id, resolved_by)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    from app.execution.engine import ExecutionEngine
    engine = ExecutionEngine(async_session_maker)
    success = await engine.resume_instance(instance_id)
    return {"approval": result, "resumed": success}

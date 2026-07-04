from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session
from app.flow_definitions.schemas import (
    FlowExecutionLogSchema,
    FlowExecutionLogCreateSchema,
)
from app.services.flow_execution_log_service import FlowExecutionLogService

router = APIRouter(
    prefix="/api/flow-execution-logs",
    tags=["Flow Execution Logs"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=FlowExecutionLogSchema, status_code=201,
             summary="Create an execution log entry",
             description="Records a node execution event within a flow for a lead.")
async def create_flow_execution_log(
    data: FlowExecutionLogCreateSchema,
    db: AsyncSession = Depends(get_db_session),
):
    service = FlowExecutionLogService(db)
    return await service.create(data)


@router.get("/", response_model=List[FlowExecutionLogSchema],
            summary="List execution logs",
            description="Returns paginated execution logs, optionally filtered by flow definition, lead, or running instance.")
async def list_flow_execution_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    flow_definition_id: Optional[UUID] = Query(None, description="Filter by flow definition ID"),
    lead_id: Optional[int] = Query(None, description="Filter by lead ID"),
    running_instance_id: Optional[UUID] = Query(None, description="Filter by running instance ID"),
    db: AsyncSession = Depends(get_db_session),
):
    service = FlowExecutionLogService(db)
    return await service.list(
        skip=skip, limit=limit,
        flow_definition_id=flow_definition_id,
        lead_id=lead_id,
        running_instance_id=running_instance_id,
    )


@router.get("/{log_id}", response_model=FlowExecutionLogSchema,
            summary="Get execution log by ID",
            description="Returns a single flow execution log entry.")
async def get_flow_execution_log(
    log_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    service = FlowExecutionLogService(db)
    try:
        return await service.get(log_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{log_id}", status_code=204,
               summary="Delete execution log",
               description="Deletes a flow execution log entry.")
async def delete_flow_execution_log(
    log_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    service = FlowExecutionLogService(db)
    deleted = await service.delete(log_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"FlowExecutionLog {log_id} not found")

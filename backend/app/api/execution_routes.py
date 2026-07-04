"""Execution Engine API — test execution endpoint, owned by the Execution Engine."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session
from app.execution.engine import ExecutionEngine

router = APIRouter(
    prefix="/api/execution",
    tags=["Execution Engine"],
)


class TestExecutionRequest(BaseModel):
    journey_id: str
    lead_id: int
    stage_key: str


@router.post("/test", summary="Test journey execution",
             description="Executes a journey for a given lead and stage key. "
                         "Owned by the Execution Engine — not the Journey API.")
async def test_execution(
    payload: TestExecutionRequest,
    db: AsyncSession = Depends(get_db_session),
):
    engine = ExecutionEngine()
    success = await engine.test_execution(payload.journey_id, payload.lead_id, payload.stage_key)

    return {
        "success": success,
        "lead_id": payload.lead_id,
        "trigger_stage_key": payload.stage_key,
        "journey_id": payload.journey_id,
    }

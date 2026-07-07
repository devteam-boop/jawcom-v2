import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from app.services.running_instance_service import RunningInstanceService

logger = logging.getLogger(__name__)


class ApprovalService:
    """Manages approvals stored in RunningJourneyInstance.data JSON column."""

    def __init__(self, instance_service: RunningInstanceService):
        self._instance_service = instance_service

    async def list_approvals(self, instance_id: UUID) -> List[dict]:
        instance = await self._instance_service.get(instance_id)
        data = instance.data or {}
        approvals_dict = data.get("approvals") or {}
        return list(approvals_dict.values())

    async def get_approval(self, instance_id: UUID, approval_id: str) -> Optional[dict]:
        instance = await self._instance_service.get(instance_id)
        data = instance.data or {}
        approvals_dict = data.get("approvals") or {}
        return approvals_dict.get(approval_id)

    async def approve(self, instance_id: UUID, approval_id: str, resolved_by: str = "system") -> dict:
        instance = await self._instance_service.get(instance_id)
        data = dict(instance.data or {})
        approvals_dict = dict(data.get("approvals") or {})
        approval = approvals_dict.get(approval_id)
        if not approval:
            raise ValueError(f"Approval {approval_id} not found in instance {instance_id}")
        if approval.get("status") != "pending":
            raise ValueError(f"Approval {approval_id} is already {approval['status']}")

        approval["status"] = "approved"
        approval["resolved_at"] = datetime.utcnow().isoformat()
        approval["resolved_by"] = resolved_by
        approval["resolution"] = "approved"
        approvals_dict[approval_id] = approval
        data["approvals"] = approvals_dict
        data.pop("_pause_reason", None)
        data.pop("_pause_node_id", None)
        data.pop("current_approval_id", None)

        await self._instance_service.update(instance_id, type("", (), {"model_dump": lambda self, **kw: {"data": data}})())
        logger.info("Approval %s approved by %s for instance %s", approval_id, resolved_by, instance_id)
        return approval

    async def reject(self, instance_id: UUID, approval_id: str, resolved_by: str = "system") -> dict:
        instance = await self._instance_service.get(instance_id)
        data = dict(instance.data or {})
        approvals_dict = dict(data.get("approvals") or {})
        approval = approvals_dict.get(approval_id)
        if not approval:
            raise ValueError(f"Approval {approval_id} not found in instance {instance_id}")
        if approval.get("status") != "pending":
            raise ValueError(f"Approval {approval_id} is already {approval['status']}")

        approval["status"] = "rejected"
        approval["resolved_at"] = datetime.utcnow().isoformat()
        approval["resolved_by"] = resolved_by
        approval["resolution"] = "rejected"
        approvals_dict[approval_id] = approval
        data["approvals"] = approvals_dict
        data.pop("_pause_reason", None)
        data.pop("_pause_node_id", None)
        data.pop("current_approval_id", None)

        await self._instance_service.update(instance_id, type("", (), {"model_dump": lambda self, **kw: {"data": data}})())
        logger.info("Approval %s rejected by %s for instance %s", approval_id, resolved_by, instance_id)
        return approval

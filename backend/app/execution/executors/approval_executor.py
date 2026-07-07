import logging
from datetime import datetime
from uuid import uuid4

from .base import BaseNodeExecutor, ExecutionResult, ExecutionContext

logger = logging.getLogger(__name__)


class ApprovalExecutor(BaseNodeExecutor):

    @property
    def node_type(self) -> str:
        return "approval"

    async def execute(self, node, running_instance, lead_id, context, exec_ctx=None):
        node_config = node.get("config") or {}
        renderer = exec_ctx.renderer if exec_ctx else None

        approval_id = str(uuid4())
        title = renderer.render(node_config.get("title", "")) if renderer else node_config.get("title", "")
        description = renderer.render(node_config.get("description", "")) if renderer else node_config.get("description", "")
        approver = renderer.render(node_config.get("approver", "")) if renderer else node_config.get("approver", "")
        approval_type = node_config.get("approval_type", "approve_reject")
        timeout = node_config.get("timeout", 86400)

        approval_data = {
            "id": approval_id,
            "node_id": node.get("id", ""),
            "title": title,
            "description": description,
            "approver": approver,
            "approval_type": approval_type,
            "timeout": timeout,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "resolved_at": None,
            "resolved_by": None,
            "resolution": None,
        }

        logger.info("Approval node %s — created approval %s: %s", node.get("id"), approval_id, title)

        return ExecutionResult(
            success=True,
            status="skipped",
            updated_context={
                "_halt": "approval",
                "_halt_node_id": node.get("id", ""),
                "approval_id": approval_id,
                "_approval_data": approval_data,
            },
            output={
                "approval_id": approval_id,
                "title": title,
                "approver": approver,
                "status": "pending",
            },
        )

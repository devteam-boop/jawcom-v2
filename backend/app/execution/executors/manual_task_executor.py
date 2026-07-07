import logging
from datetime import datetime
from uuid import uuid4

from .base import BaseNodeExecutor, ExecutionResult, ExecutionContext

logger = logging.getLogger(__name__)


class ManualTaskExecutor(BaseNodeExecutor):

    @property
    def node_type(self) -> str:
        return "manual_task"

    async def execute(self, node, running_instance, lead_id, context, exec_ctx=None):
        node_config = node.get("config") or {}
        renderer = exec_ctx.renderer if exec_ctx else None

        task_id = str(uuid4())
        title = renderer.render(node_config.get("title", "")) if renderer else node_config.get("title", "")
        description = renderer.render(node_config.get("description", "")) if renderer else node_config.get("description", "")
        assignee = renderer.render(node_config.get("assignee", "")) if renderer else node_config.get("assignee", "")
        priority = node_config.get("priority", "medium")
        due_date = node_config.get("due_date", "")

        task_data = {
            "id": task_id,
            "node_id": node.get("id", ""),
            "title": title,
            "description": description,
            "assignee": assignee,
            "priority": priority,
            "due_date": due_date,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "completed_by": None,
        }

        logger.info("ManualTask node %s — created task %s: %s", node.get("id"), task_id, title)

        return ExecutionResult(
            success=True,
            status="skipped",
            updated_context={
                "_halt": "task",
                "_halt_node_id": node.get("id", ""),
                "task_id": task_id,
                "_task_data": task_data,
            },
            output={
                "task_id": task_id,
                "title": title,
                "assignee": assignee,
                "priority": priority,
                "status": "pending",
            },
        )

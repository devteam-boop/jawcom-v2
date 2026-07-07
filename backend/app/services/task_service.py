import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from app.services.running_instance_service import RunningInstanceService

logger = logging.getLogger(__name__)


class TaskService:
    """Manages manual tasks stored in RunningJourneyInstance.data JSON column."""

    def __init__(self, instance_service: RunningInstanceService):
        self._instance_service = instance_service

    async def list_tasks(self, instance_id: UUID) -> List[dict]:
        instance = await self._instance_service.get(instance_id)
        data = instance.data or {}
        tasks_dict = data.get("tasks") or {}
        return list(tasks_dict.values())

    async def get_task(self, instance_id: UUID, task_id: str) -> Optional[dict]:
        instance = await self._instance_service.get(instance_id)
        data = instance.data or {}
        tasks_dict = data.get("tasks") or {}
        return tasks_dict.get(task_id)

    async def complete_task(self, instance_id: UUID, task_id: str, completed_by: str = "system") -> dict:
        instance = await self._instance_service.get(instance_id)
        data = dict(instance.data or {})
        tasks_dict = dict(data.get("tasks") or {})
        task = tasks_dict.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found in instance {instance_id}")
        if task.get("status") != "pending":
            raise ValueError(f"Task {task_id} is already {task['status']}")

        task["status"] = "completed"
        task["completed_at"] = datetime.utcnow().isoformat()
        task["completed_by"] = completed_by
        tasks_dict[task_id] = task
        data["tasks"] = tasks_dict
        data.pop("_pause_reason", None)
        data.pop("_pause_node_id", None)
        data.pop("current_task_id", None)

        await self._instance_service.update(instance_id, type("", (), {"model_dump": lambda self, **kw: {"data": data}})())
        logger.info("Task %s completed by %s for instance %s", task_id, completed_by, instance_id)
        return task

    async def reject_task(self, instance_id: UUID, task_id: str, completed_by: str = "system") -> dict:
        instance = await self._instance_service.get(instance_id)
        data = dict(instance.data or {})
        tasks_dict = dict(data.get("tasks") or {})
        task = tasks_dict.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found in instance {instance_id}")
        if task.get("status") != "pending":
            raise ValueError(f"Task {task_id} is already {task['status']}")

        task["status"] = "rejected"
        task["completed_at"] = datetime.utcnow().isoformat()
        task["completed_by"] = completed_by
        tasks_dict[task_id] = task
        data["tasks"] = tasks_dict
        data.pop("_pause_reason", None)
        data.pop("_pause_node_id", None)
        data.pop("current_task_id", None)

        await self._instance_service.update(instance_id, type("", (), {"model_dump": lambda self, **kw: {"data": data}})())
        logger.info("Task %s rejected by %s for instance %s", task_id, completed_by, instance_id)
        return task

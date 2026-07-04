"""ExecutorFactory — central registry for node executors.

Adding a new node type requires ONLY:
    1. Create a new executor class inheriting BaseNodeExecutor.
    2. Import and register it here.

No changes to ExecutionEngine are required.
"""

import logging
from typing import Dict, Type

from .base import BaseNodeExecutor
from .trigger_executor import TriggerExecutor
from .condition_executor import ConditionExecutor
from .wait_executor import WaitExecutor
from .delay_executor import DelayExecutor
from .send_whatsapp_executor import SendWhatsAppExecutor
from .send_email_executor import SendEmailExecutor
from .notification_executor import NotificationExecutor
from .end_executor import EndExecutor

logger = logging.getLogger(__name__)


class ExecutorFactory:
    """Registry mapping node type strings to executor classes."""

    _executors: Dict[str, Type[BaseNodeExecutor]] = {
        "trigger": TriggerExecutor,
        "condition": ConditionExecutor,
        "delay": DelayExecutor,
        "wait": WaitExecutor,
        "send_whatsapp": SendWhatsAppExecutor,
        "send_email": SendEmailExecutor,
        "notification": NotificationExecutor,
        "end": EndExecutor,
    }

    @classmethod
    def register(cls, node_type: str, executor_class: Type[BaseNodeExecutor]) -> None:
        """Register a new node executor for *node_type*."""
        cls._executors[node_type] = executor_class
        logger.info("Executor registered for node type %s", node_type)

    @classmethod
    def get(cls, node_type: str) -> BaseNodeExecutor:
        """Return an instance of the executor for *node_type*.

        Raises:
            ValueError: when no executor exists for the requested node type.
        """
        executor_class = cls._executors.get(node_type)
        if executor_class is None:
            raise ValueError(f"No executor registered for node type: {node_type}")
        return executor_class()

    @classmethod
    def list_registered(cls) -> Dict[str, str]:
        """Return a mapping of node type -> executor class name."""
        return {k: v.__name__ for k, v in cls._executors.items()}

"""Executors package.

Exports the public framework surface: base contract, result object, factory
and the registry of built-in executors.
"""

from .base import BaseNodeExecutor, ExecutionResult, ExecutionContext
from .factory import ExecutorFactory
from .trigger_executor import TriggerExecutor
from .condition_executor import ConditionExecutor
from .wait_executor import WaitExecutor
from .delay_executor import DelayExecutor
from .send_whatsapp_executor import SendWhatsAppExecutor
from .send_email_executor import SendEmailExecutor
from .notification_executor import NotificationExecutor
from .end_executor import EndExecutor

__all__ = [
    "BaseNodeExecutor",
    "ExecutionContext",
    "ExecutionResult",
    "ExecutorFactory",
    "TriggerExecutor",
    "ConditionExecutor",
    "WaitExecutor",
    "DelayExecutor",
    "SendWhatsAppExecutor",
    "SendEmailExecutor",
    "NotificationExecutor",
    "EndExecutor",
]

"""Send WhatsApp node executor.

For Sprint 2 this executor does NOT call the WhatsApp API. It creates an
execution log, sleeps 100ms to simulate network latency, and returns success.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict

from .base import BaseNodeExecutor, ExecutionResult
from .utils import build_log_payload

logger = logging.getLogger(__name__)


class SendWhatsAppExecutor(BaseNodeExecutor):
    """Executor for flow send_whatsapp nodes."""

    @property
    def node_type(self) -> str:
        return "send_whatsapp"

    async def execute(
        self,
        node: Dict[str, Any],
        running_instance: Any,
        lead_id: int,
        context: Dict[str, Any],
    ) -> ExecutionResult:
        started_at = datetime.utcnow()
        node_data = node.get("data") or {}
        node_id = node.get("id", "send_whatsapp")

        template_id = node_data.get("template_id", "welcome_whatsapp")
        variable_mapping = node_data.get("variable_mapping", {})

        logger.info(
            "SendWhatsAppExecutor: simulating send for lead=%s node=%s template=%s",
            lead_id, node_id, template_id,
        )

        # Sprint 2 dummy behaviour: do not integrate external API.
        await asyncio.sleep(0.1)

        output_data = {
            "message": "WhatsApp message simulated",
            "template_id": template_id,
            "variable_mapping": variable_mapping,
        }

        output = {
            "log_payload": build_log_payload(
                flow_definition_id=context.get("flow_definition_id", ""),
                running_instance_id=str(running_instance.id),
                lead_id=lead_id,
                node_id=node_id,
                node_type=self.node_type,
                status="success",
                input_data={"template_id": template_id},
                output_data=output_data,
                started_at=started_at,
            ),
            **output_data,
        }

        return ExecutionResult(
            success=True,
            updated_context=context,
            status="success",
            output=output,
        )

"""JAWIS Lead Provider — fetches real lead/company/owner data from JAWIS API.

Implements the ``LeadProvider`` interface so the execution engine can switch
from ``DummyLeadProvider`` to live JAWIS data by configuration alone.
"""

import logging
from typing import Any, Dict

from app.jawis.client import get_jawis_client

from .lead_provider import LeadProvider

logger = logging.getLogger(__name__)


class JawisLeadProvider(LeadProvider):
    """Fetches lead context from the JAWIS Business OS API.

    Returns the same dict shape as ``DummyLeadProvider`` so the engine
    and executors require zero changes.
    """

    async def get_lead_context(self, lead_id: int) -> Dict[str, Any]:
        client = get_jawis_client()
        ctx = await client.get_lead_context(str(lead_id))

        if ctx is None:
            logger.warning("JAWIS lead context not found for lead_id=%s, falling back to empty context", lead_id)
            return {
                "lead": {"id": lead_id, "name": "Unknown", "email": None, "phone": None, "stage_key": None},
                "company": None,
                "owner": None,
                "stage": None,
            }

        lead = ctx.lead
        company = ctx.company
        stage = ctx.stage
        owner = ctx.assigned_user

        result: Dict[str, Any] = {
            "lead": {
                "id": lead.id,
                "name": lead.name,
                "email": lead.email,
                "phone": lead.phone,
                "stage_key": lead.stage_key,
                "company_id": lead.company_id,
                "assigned_to": lead.assigned_to,
                "custom_fields": dict(lead.metadata or {}),
            },
            "company": {
                "id": company.id,
                "name": company.name,
                "industry": company.industry,
                "size": company.size,
                "website": company.website,
                "custom_fields": dict(company.metadata or {}),
            } if company else None,
            "owner": {
                "id": owner.id,
                "name": owner.name,
                "email": owner.email,
                "role": owner.role,
            } if owner else None,
            "stage": {
                "key": stage.key,
                "name": stage.name,
                "order": stage.order,
            } if stage else None,
        }

        logger.info(
            "JAWIS lead context resolved for lead_id=%s lead=%s company=%s owner=%s stage=%s",
            lead_id, lead.name,
            company.name if company else "N/A",
            owner.name if owner else "N/A",
            stage.name if stage else "N/A",
        )

        return result

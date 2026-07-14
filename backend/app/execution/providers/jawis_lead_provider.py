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
            # Only reached on a genuine failure now (lead not found, no
            # stage on the lead, or a request error) — not on every call,
            # as it was before client.get_lead_context() was fixed (it
            # previously crashed on lead.stage_key, which doesn't exist on
            # the lightweight lead JAWIS actually returns, and this
            # fallback masked that as a normal "Unknown"/null-phone send).
            logger.warning(
                "JAWIS lead context genuinely unavailable for lead_id=%s (see prior error/warning log for why) "
                "— falling back to an empty context; downstream send will lack a real phone/email",
                lead_id,
            )
            fallback = {
                "lead": {"id": lead_id, "name": "Unknown", "email": None, "phone": None},
                "company": None,
                "owner": None,
                "stage": None,
            }
            logger.info("Lead context before executor (lead_id=%s): %s", lead_id, fallback)
            return fallback

        lead = ctx.lead
        company = ctx.company
        stage = ctx.stage
        owner = ctx.assigned_user

        # lead is a LeadSummarySchema (id/name/email/phone/city/stage) —
        # company_id/assigned_to/metadata are no longer part of what JAWIS
        # returns for a lead, so they're not read here; company/owner stay
        # None (client.get_lead_context() no longer fetches them either —
        # nothing left to fetch them by).
        result: Dict[str, Any] = {
            "lead": {
                "id": lead.id,
                "name": lead.name,
                "email": lead.email,
                "phone": lead.phone,
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
            "JAWIS lead context resolved for lead_id=%s lead=%s phone=%s email=%s stage=%s",
            lead_id, lead.name, lead.phone, lead.email,
            stage.name if stage else "N/A",
        )
        logger.info("Lead context before executor (lead_id=%s): %s", lead_id, result)
        return result

from fastapi import APIRouter

from app.integrations import IntegrationFactory, IntegrationConfig

router = APIRouter(
    prefix="/api/integrations",
    tags=["Integrations"],
)


@router.get("/health", response_model=dict,
            summary="Integration health",
            description="Live health status for WhatsApp, Email, CRM (dummy|jawis alias) and JAWIS, for dashboard display.")
async def get_integrations_health():
    whatsapp = await IntegrationFactory.get("whatsapp").health()
    email = await IntegrationFactory.get("email").health()
    crm = await IntegrationFactory.get("crm").health()

    cfg = IntegrationConfig()
    jawis_configured = bool(cfg.jawis_base_url and cfg.jawis_api_key)
    jawis = {
        "status": "healthy" if jawis_configured else "unconfigured",
        "name": "jawis",
        "configured": jawis_configured,
        "lead_provider": cfg.jawis_lead_provider,
        "crm_provider": cfg.jawis_crm_provider,
    }

    return {
        "whatsapp": whatsapp,
        "email": email,
        "crm": crm,
        "jawis": jawis,
    }

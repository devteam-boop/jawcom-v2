from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.config.logging import configure_logging, get_logger
from app.core.dependencies import get_db_session
from app.database.session import init_db, close_db, async_session_maker
from app.api import (
    journey_router,
    stage_mapping_router,
    running_instance_router,
    flow_definition_router,
    flow_version_router,
    flow_execution_log_router,
    execution_router,
    approval_router,
    task_router,
    journey_event_router,
    template_router,
    whatsapp_template_router,
    integration_router,
    communication_event_router,
    meta_webhook_router,
    resend_webhook_router,
    ai_assistant_router,
    ai_summary_router,
    message_router,
    debug_router,
    email_sync_router,
    lead_timeline_router,
    lead_journey_router,
    auth_router,
    admin_account_router,
    ai_text_router,
)
from app.events.dispatcher import get_dispatcher
from app.jawis.webhook import get_webhook_handler
from app.core.jawis_auth_middleware import JawisAuthMiddleware

# Configure logging
configure_logging()
logger = get_logger(__name__)

# Get settings
settings = get_settings()

if settings.CORS_ALLOW_CREDENTIALS and "*" in settings.cors_origins:
    # Wildcard origins + credentialed requests must never be combined —
    # any site could then read authenticated responses. CORS_ORIGINS must
    # be an explicit, comma-separated allowlist (e.g.
    # "https://jawcom-v2.vercel.app") whenever CORS_ALLOW_CREDENTIALS is
    # true. Fails loud at startup rather than silently wildcarding.
    raise RuntimeError(
        "CORS_ALLOW_CREDENTIALS=true requires an explicit CORS_ORIGINS allowlist — "
        "got '*'. Set CORS_ORIGINS to a comma-separated list of exact origins."
    )

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    description="JawCom Communication OS Backend Foundation",
    version=settings.VERSION,
)

# Registration order here is load-bearing, not incidental: Starlette's
# app.add_middleware() prepends (LIFO) — the LAST middleware added ends up
# OUTERMOST, running first on the way in. JawisAuthMiddleware must be
# added BEFORE CORSMiddleware so CORSMiddleware ends up outermost and can
# short-circuit OPTIONS preflight (and attach CORS headers to every
# response, including 401s) before the request ever reaches the auth
# check. Registering them in the opposite order (as this file previously
# did) makes the auth middleware run first: it 401s bare, unauthenticated
# preflight requests before CORSMiddleware gets a chance to run at all, so
# the browser never sees an Access-Control-Allow-Origin header and reports
# it as a CORS failure — this was the actual root cause of the production
# "blocked by CORS" errors on /api/messages/*, not a CORS config problem.

# Auth gate for the whole app: JAWIS bearer-token auth on
# /api/leads/{lead_id}/journey/*, JAWIS-or-admin-session on /api/messages/*,
# and an admin session cookie required everywhere else under /api/* — see
# app/core/jawis_auth_middleware.py.
app.add_middleware(JawisAuthMiddleware)

# Add CORS middleware LAST so it wraps outermost (see note above).
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)


# Include Journey Engine routers
app.include_router(journey_router)
app.include_router(stage_mapping_router)
app.include_router(running_instance_router)

# Include Flow Definition Engine routers
app.include_router(flow_definition_router)
app.include_router(flow_version_router)
app.include_router(flow_execution_log_router)
app.include_router(execution_router)
app.include_router(approval_router)
app.include_router(task_router)
app.include_router(journey_event_router)
app.include_router(template_router)
app.include_router(whatsapp_template_router)
app.include_router(integration_router)
app.include_router(communication_event_router)
app.include_router(meta_webhook_router)
app.include_router(resend_webhook_router)
app.include_router(ai_assistant_router)
app.include_router(ai_summary_router)
app.include_router(message_router)
app.include_router(debug_router)
app.include_router(email_sync_router)
app.include_router(lead_timeline_router)
app.include_router(lead_journey_router)
app.include_router(auth_router)
app.include_router(admin_account_router)
app.include_router(ai_text_router)


_scheduler = None


@app.on_event("startup")
async def startup_event():
    """Initialize database and register event handlers on startup."""
    await init_db()

    # Register the communication event handler with the execution engine
    from app.events.handlers import CommunicationEventHandler
    from app.execution.engine import ExecutionEngine

    dispatcher = get_dispatcher()
    engine = ExecutionEngine()
    handler = CommunicationEventHandler(execution_engine=engine)

    for event_type in ("lead.created", "lead.stage_changed", "lead.assigned", "lead.requirement_met"):
        dispatcher.register_handler(event_type, handler)

    logger.info(
        "Registered CommunicationEventHandler for %d event types",
        len(("lead.created", "lead.stage_changed", "lead.assigned", "lead.requirement_met")),
    )

    # Start background scheduler for waiting instances
    if settings.SCHEDULER_ENABLED:
        from app.services.wait_scheduler_service import SchedulerService

        global _scheduler
        _scheduler = SchedulerService(async_session_maker)
        await _scheduler.start()

    logger.info("Application startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection and stop background tasks on shutdown."""
    global _scheduler
    if _scheduler is not None:
        await _scheduler.stop()
        _scheduler = None

    await close_db()
    logger.info("Application shutdown complete")


@app.get("/health", tags=["Health"])
async def health_check(db: AsyncSession = Depends(get_db_session)):
    """Health check endpoint."""
    try:
        # Test database connection
        await db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }


# ── JAWIS Event Bridge ─────────────────────────────────────────────

@app.post("/api/webhooks/jawis", tags=["Webhooks"])
async def jawis_webhook(payload: dict):
    """Receive a business event from JAWIS and trigger journey orchestration.

    Expected payload:
    .. code-block:: json

        {
            "event_id": "…",
            "event_type": "lead.stage_changed",
            "timestamp": "…",
            "source": "jawis",
            "data": {
                "lead_id": "<uuid>",
                "from_stage_key": "lead_identified",
                "to_stage_key": "lead_qualified"
            }
        }
    """
    handler = get_webhook_handler()
    return await handler.handle_webhook(payload)

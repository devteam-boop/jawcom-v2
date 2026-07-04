from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.config.logging import configure_logging, get_logger
from app.core.dependencies import get_db_session
from app.database.session import init_db, close_db
from app.api import (
    journey_router,
    stage_mapping_router,
    running_instance_router,
    flow_definition_router,
    flow_version_router,
    flow_execution_log_router,
    execution_router,
)
from app.events.dispatcher import get_dispatcher
from app.jawis.webhook import get_webhook_handler

# Configure logging
configure_logging()
logger = get_logger(__name__)

# Get settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    description="JawCom Communication OS Backend Foundation",
    version=settings.VERSION,
)

# Add CORS middleware
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
    logger.info("Application startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown."""
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

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.config.logging import configure_logging, get_logger
from app.core.dependencies import get_db_session
from app.database.session import init_db, close_db

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


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    await init_db()
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
        await db.execute("SELECT 1")
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

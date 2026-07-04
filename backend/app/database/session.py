"""Database session management for the application."""

import logging

from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config.settings import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# Create async engine with production-ready settings
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # Set to False in production
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_size=10,  # Number of connections to maintain
    max_overflow=20,  # Additional connections beyond pool_size
)

# Create sessionmaker
async_session_maker = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db():
    """Initialize database connection."""
    logger.info("Initializing database connection")
    # The engine will be initialized when first used
    pass


async def close_db():
    """Close database connection."""
    logger.info("Closing database connection")
    await engine.dispose()


async def get_db() -> AsyncSession:
    """FastAPI dependency for getting database session."""
    async with async_session_maker() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


# Add connection event listeners for monitoring
@event.listens_for(engine.sync_engine, "connect")
def on_connect(dbapi_connection, connection_record):
    """Log when a new database connection is established."""
    logger.info("New database connection established")


@event.listens_for(engine.sync_engine, "close")
def on_close(dbapi_connection, connection_record):
    """Log when a database connection is closed."""
    logger.info("Database connection closed")


@event.listens_for(engine.sync_engine, "checkout")
def on_checkout(dbapi_connection, connection_record, connection_proxy):
    """Log when a connection is checked out from the pool."""
    logger.debug("Connection checked out from pool")


@event.listens_for(engine.sync_engine, "checkin")
def on_checkin(dbapi_connection, connection_record):
    """Log when a connection is checked back into the pool."""
    logger.debug("Connection checked in to pool")

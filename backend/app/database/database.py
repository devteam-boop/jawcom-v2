"""Database connection and engine management."""

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import AsyncAdaptedQueuePool

from app.config.settings import get_settings

settings = get_settings()


def create_engine():
    """Create and configure the async database engine."""
    return create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DATABASE_ECHO,
        poolclass=AsyncAdaptedQueuePool,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    )


engine = create_engine()


async def get_db_session():
    """Get a database session."""
    from app.database.session import async_session_maker
    async with async_session_maker() as session:
        yield session

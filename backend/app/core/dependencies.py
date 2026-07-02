"""FastAPI dependencies for the application."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency to get database session."""
    async for session in get_db():
        yield session

"""Base service with common business logic."""

from typing import Generic, List, Optional, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType")


class BaseService(Generic[ModelType]):
    """Base service with common business operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, id: int) -> Optional[ModelType]:
        """Get an entity by ID."""
        raise NotImplementedError

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Get all entities with pagination."""
        raise NotImplementedError

    async def create(self, obj: ModelType) -> ModelType:
        """Create a new entity."""
        raise NotImplementedError

    async def update(self, id: int, obj: ModelType) -> ModelType:
        """Update an existing entity."""
        raise NotImplementedError

    async def delete(self, id: int) -> bool:
        """Delete an entity by ID."""
        raise NotImplementedError

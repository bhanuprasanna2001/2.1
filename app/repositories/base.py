"""Base repository with generic CRUD operations."""

from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic repository providing common CRUD operations.

    This base class implements the repository pattern, abstracting
    database operations from business logic.

    Attributes:
        model: The SQLAlchemy model class this repository manages.
        session: The async database session.
    """

    def __init__(self, model: type[ModelType], session: AsyncSession) -> None:
        """Initialize repository with model and session.

        Args:
            model: SQLAlchemy model class.
            session: Async database session.
        """
        self.model = model
        self.session = session

    async def create(self, **kwargs: Any) -> ModelType:
        """Create a new entity.

        Args:
            **kwargs: Fields to set on the new entity.

        Returns:
            The created entity.
        """
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def get_by_id(self, entity_id: UUID) -> ModelType | None:
        """Get an entity by its ID.

        Args:
            entity_id: The entity's UUID.

        Returns:
            The entity if found, None otherwise.
        """
        result = await self.session.execute(
            select(self.model).where(self.model.id == entity_id)  # type: ignore[attr-defined]
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        order_by: Any | None = None,
    ) -> list[ModelType]:
        """Get all entities with pagination.

        Args:
            offset: Number of records to skip.
            limit: Maximum number of records to return.
            order_by: Column to order by.

        Returns:
            List of entities.
        """
        query = select(self.model)

        if order_by is not None:
            query = query.order_by(order_by)
        else:
            # Default ordering by created_at desc if available
            if hasattr(self.model, "created_at"):
                query = query.order_by(
                    self.model.created_at.desc()  # type: ignore[attr-defined]
                )

        query = query.offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(
        self,
        entity: ModelType,
        **kwargs: Any,
    ) -> ModelType:
        """Update an entity with given fields.

        Args:
            entity: The entity to update.
            **kwargs: Fields to update.

        Returns:
            The updated entity.
        """
        for key, value in kwargs.items():
            if hasattr(entity, key):
                setattr(entity, key, value)

        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def delete(self, entity: ModelType) -> None:
        """Delete an entity.

        Args:
            entity: The entity to delete.
        """
        await self.session.delete(entity)
        await self.session.flush()

    async def count(self) -> int:
        """Count total number of entities.

        Returns:
            Total count.
        """
        result = await self.session.execute(select(func.count()).select_from(self.model))
        return result.scalar_one()

    async def exists(self, entity_id: UUID) -> bool:
        """Check if an entity exists.

        Args:
            entity_id: The entity's UUID.

        Returns:
            True if exists, False otherwise.
        """
        result = await self.session.execute(
            select(func.count()).where(self.model.id == entity_id)  # type: ignore[attr-defined]
        )
        return result.scalar_one() > 0

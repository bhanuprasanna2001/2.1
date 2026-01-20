"""Base model class and mixins for SQLAlchemy models."""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models.

    Provides common functionality and configuration for all models.
    """

    # Generate __tablename__ automatically from class name
    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Generate table name from class name (e.g., UserProfile -> user_profiles)."""
        name = cls.__name__
        # Convert CamelCase to snake_case and pluralize
        import re

        snake_case = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
        # Simple pluralization (add 's', handle 'y' -> 'ies')
        if snake_case.endswith("y"):
            return snake_case[:-1] + "ies"
        return snake_case + "s"

    def to_dict(self) -> dict[str, Any]:
        """Convert model instance to dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class TimestampMixin:
    """Mixin for adding created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

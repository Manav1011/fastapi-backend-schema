"""
Django-like model methods (save, delete, refresh, etc.).

This mixin adds Django-like methods to models.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from project.core.db.base import Base


class ModelMethodsMixin:
    """
    Mixin that adds Django-like methods to models.
    
    Usage:
        class MyModel(Base, ModelMethodsMixin):
            ...
        
        # In your route/service:
        async with get_async_session() as session:
            obj = MyModel(name="test")
            await obj.save(session)
            await obj.delete(session)
            await obj.refresh(session)
    """

    async def save(
        self: "Base",
        session: AsyncSession,
        *,
        commit: bool = True,
        send_signals: bool = True,
    ) -> "Base":
        """
        Save the instance to the database (Django-like).
        
        Args:
            session: The async database session
            commit: Whether to commit the transaction (default: True)
            send_signals: Whether to send pre_save/post_save signals (default: True)
        
        Returns:
            Self (for chaining)
        """
        from project.core.db import post_save, pre_save

        # Check if this is a new instance
        is_new = inspect(self).persistent is False

        # Send pre_save signal
        if send_signals:
            await pre_save.send(sender=type(self), instance=self)

        # Add to session
        session.add(self)
        await session.flush()

        # Send post_save signal
        if send_signals:
            await post_save.send(sender=type(self), instance=self, created=is_new)

        # Commit if requested
        if commit:
            await session.commit()
            # Refresh to get any database-generated values
            await session.refresh(self)

        return self

    async def delete(
        self: "Base",
        session: AsyncSession,
        *,
        commit: bool = True,
        send_signals: bool = True,
    ) -> None:
        """
        Delete the instance from the database (Django-like).
        
        Args:
            session: The async database session
            commit: Whether to commit the transaction (default: True)
            send_signals: Whether to send pre_delete/post_delete signals (default: True)
        """
        from project.core.db import post_delete, pre_delete

        # Send pre_delete signal
        if send_signals:
            await pre_delete.send(sender=type(self), instance=self)

        # Delete from session
        await session.delete(self)
        await session.flush()

        # Send post_delete signal
        if send_signals:
            await post_delete.send(sender=type(self), instance=self)

        # Commit if requested
        if commit:
            await session.commit()

    async def refresh(
        self: "Base",
        session: AsyncSession,
        *,
        attribute_names: Optional[list[str]] = None,
    ) -> "Base":
        """
        Refresh the instance from the database (Django-like).
        
        Args:
            session: The async database session
            attribute_names: Optional list of attribute names to refresh
        
        Returns:
            Self (for chaining)
        """
        await session.refresh(self, attribute_names=attribute_names)
        return self

    async def update(
        self: "Base",
        session: AsyncSession,
        **kwargs: Any,
    ) -> "Base":
        """
        Update instance attributes and save (Django-like).
        
        Args:
            session: The async database session
            **kwargs: Attributes to update
        
        Returns:
            Self (for chaining)
        
        Example:
            await user.update(session, name="New Name", email="new@example.com")
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return await self.save(session)

    @classmethod
    async def create(
        cls: type["Base"],
        session: AsyncSession,
        **kwargs: Any,
    ) -> "Base":
        """
        Create and save a new instance (Django-like).
        
        Args:
            session: The async database session
            **kwargs: Attributes for the new instance
        
        Returns:
            The created instance
        
        Example:
            user = await User.create(session, email="test@example.com", name="Test")
        """
        instance = cls(**kwargs)
        return await instance.save(session)

    @classmethod
    async def get_or_create(
        cls: type["Base"],
        session: AsyncSession,
        defaults: Optional[dict[str, Any]] = None,
        **lookup: Any,
    ) -> tuple["Base", bool]:
        """
        Get an instance or create it if it doesn't exist (Django-like).
        
        Args:
            session: The async database session
            defaults: Default values to use when creating
            **lookup: Lookup parameters
        
        Returns:
            Tuple of (instance, created)
        
        Example:
            user, created = await User.get_or_create(
                session,
                email="test@example.com",
                defaults={"name": "Test User"}
            )
        """
        from sqlalchemy import select

        # Try to get existing instance
        stmt = select(cls)
        for key, value in lookup.items():
            stmt = stmt.where(getattr(cls, key) == value)

        result = await session.execute(stmt)
        instance = result.scalar_one_or_none()

        if instance is not None:
            return (instance, False)

        # Create new instance
        create_kwargs = {**lookup}
        if defaults:
            create_kwargs.update(defaults)
        instance = cls(**create_kwargs)
        await instance.save(session)
        return (instance, True)

    @classmethod
    async def update_or_create(
        cls: type["Base"],
        session: AsyncSession,
        defaults: Optional[dict[str, Any]] = None,
        **lookup: Any,
    ) -> tuple["Base", bool]:
        """
        Update an instance or create it if it doesn't exist (Django-like).
        
        Args:
            session: The async database session
            defaults: Values to update/create with
            **lookup: Lookup parameters
        
        Returns:
            Tuple of (instance, created)
        
        Example:
            user, created = await User.update_or_create(
                session,
                email="test@example.com",
                defaults={"name": "Updated Name"}
            )
        """
        from sqlalchemy import select

        # Try to get existing instance
        stmt = select(cls)
        for key, value in lookup.items():
            stmt = stmt.where(getattr(cls, key) == value)

        result = await session.execute(stmt)
        instance = result.scalar_one_or_none()

        if instance is not None:
            # Update existing
            if defaults:
                await instance.update(session, **defaults)
            return (instance, False)

        # Create new instance
        create_kwargs = {**lookup}
        if defaults:
            create_kwargs.update(defaults)
        instance = cls(**create_kwargs)
        await instance.save(session)
        return (instance, True)


"""
Django-like QuerySet for async SQLAlchemy models.

Provides Django-like query methods: filter(), exclude(), get(), first(), count(), etc.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, Optional, TypeVar

from sqlalchemy import Select, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from project.core.db.base import Base

ModelType = TypeVar("ModelType", bound="Base")


class QuerySet(Generic[ModelType]):
    """
    Django-like QuerySet for querying models.
    
    Usage:
        # Get all users
        users = await User.objects.all(session)
        
        # Filter users
        active_users = await User.objects.filter(session, is_active=True)
        
        # Get single user
        user = await User.objects.get(session, email="test@example.com")
        
        # Use specific database (Django-like)
        users = await User.objects.using("analytics").all(session)
        
        # Count
        count = await User.objects.count(session)
    """

    def __init__(self, model: type[ModelType], session: AsyncSession, using: Optional[str] = None):
        self.model = model
        self.session = session
        self._using = using  # Database alias (Django-like)
        self._query: Optional[Select] = None

    def _get_query(self) -> Select:
        """Get or create the base query."""
        if self._query is None:
            self._query = select(self.model)
        return self._query

    async def all(self) -> list[ModelType]:
        """
        Return all objects (Django-like).
        
        Returns:
            List of all model instances
        """
        query = self._get_query()
        result = await self.session.execute(query)
        return list(result.scalars().all())

    def filter(self, **kwargs: Any) -> QuerySet[ModelType]:
        """
        Filter objects (Django-like).
        
        Args:
            **kwargs: Field lookups (e.g., is_active=True, email="test@example.com")
        
        Returns:
            New QuerySet with filters applied
        
        Example:
            users = await User.objects(session).filter(is_active=True).all()
        """
        query = self._get_query()
        for key, value in kwargs.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
        new_qs = QuerySet(self.model, self.session, using=self._using)
        new_qs._query = query
        return new_qs

    def exclude(self, **kwargs: Any) -> QuerySet[ModelType]:
        """
        Exclude objects (Django-like).
        
        Args:
            **kwargs: Field lookups to exclude
        
        Returns:
            New QuerySet with exclusions applied
        
        Example:
            users = await User.objects(session).exclude(is_active=False).all()
        """
        query = self._get_query()
        for key, value in kwargs.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) != value)
        new_qs = QuerySet(self.model, self.session, using=self._using)
        new_qs._query = query
        return new_qs
    
    def using(self, db_alias: str) -> QuerySet[ModelType]:
        """
        Select database to use (Django-like).
        
        Note: This method sets the database alias, but you must pass
        a session from that database when calling methods like all(), get(), etc.
        
        Args:
            db_alias: Database alias (e.g., "default", "analytics")
        
        Returns:
            New QuerySet configured to use the specified database
        
        Example:
            from project.core.db.session import get_sessionmaker
            sessionmaker = get_sessionmaker("analytics")
            async with sessionmaker() as session:
                users = await User.objects.using("analytics").all(session)
        """
        new_qs = QuerySet(self.model, self.session, using=db_alias)
        new_qs._query = self._query
        return new_qs

    async def get(self, **kwargs: Any) -> ModelType:
        """
        Get a single object or raise exception (Django-like).
        
        Args:
            **kwargs: Field lookups
        
        Returns:
            Single model instance
        
        Raises:
            DoesNotExist: If no object found
            MultipleObjectsReturned: If multiple objects found
        
        Example:
            user = await User.objects.get(session, email="test@example.com")
        """
        query = self._get_query()
        for key, value in kwargs.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)

        result = await self.session.execute(query)
        instances = list(result.scalars().all())

        if len(instances) == 0:
            raise DoesNotExist(f"{self.model.__name__} matching query does not exist.")
        if len(instances) > 1:
            raise MultipleObjectsReturned(
                f"get() returned more than one {self.model.__name__} -- it returned {len(instances)}!"
            )

        return instances[0]

    async def first(self) -> Optional[ModelType]:
        """
        Get the first object or None (Django-like).
        
        Returns:
            First model instance or None
        
        Example:
            user = await User.objects.filter(session, is_active=True).first()
        """
        query = self._get_query().limit(1)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def last(self) -> Optional[ModelType]:
        """
        Get the last object or None (Django-like).
        
        Returns:
            Last model instance or None
        
        Example:
            user = await User.objects(session).order_by("-date_joined").last()
        """
        query = self._get_query()
        # Get primary key for ordering if no ordering exists
        # Check if query has order_by by checking if it's a Select object with order_by
        if not hasattr(query, '_order_by_clauses') or not query._order_by_clauses:
            pk_columns = list(self.model.__table__.primary_key.columns)
            if pk_columns:
                query = query.order_by(pk_columns[0].desc())
        query = query.limit(1)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def count(self) -> int:
        """
        Count objects (Django-like).
        
        Returns:
            Number of objects
        
        Example:
            count = await User.objects.count(session)
        """
        query = self._get_query()
        count_query = select(func.count()).select_from(query.subquery())
        result = await self.session.execute(count_query)
        return result.scalar_one()

    async def exists(self, **kwargs: Any) -> bool:
        """
        Check if objects exist (Django-like).
        
        Args:
            **kwargs: Optional field lookups
        
        Returns:
            True if objects exist, False otherwise
        
        Example:
            exists = await User.objects.exists(session, email="test@example.com")
        """
        if kwargs:
            qs = await self.filter(**kwargs)
        else:
            qs = self
        query = qs._get_query().limit(1)
        result = await self.session.execute(select(1).select_from(query.subquery()))
        return result.scalar_one_or_none() is not None

    def order_by(self, *fields: str) -> QuerySet[ModelType]:
        """
        Order queryset (Django-like).
        
        Args:
            *fields: Field names to order by (use "-field" for descending)
        
        Returns:
            New QuerySet with ordering applied
        
        Example:
            users = await User.objects.order_by("-date_joined", "email")
        """
        query = self._get_query()
        order_by_clauses = []
        for field in fields:
            if field.startswith("-"):
                field_name = field[1:]
                if hasattr(self.model, field_name):
                    order_by_clauses.append(getattr(self.model, field_name).desc())
            else:
                if hasattr(self.model, field):
                    order_by_clauses.append(getattr(self.model, field).asc())
        
        if order_by_clauses:
            query = query.order_by(*order_by_clauses)
        
        new_qs = QuerySet(self.model, self.session, using=self._using)
        new_qs._query = query
        return new_qs

    def limit(self, count: int) -> QuerySet[ModelType]:
        """
        Limit queryset (Django-like).
        
        Args:
            count: Number of objects to return
        
        Returns:
            New QuerySet with limit applied
        
        Example:
            users = await User.objects.limit(10)
        """
        query = self._get_query().limit(count)
        new_qs = QuerySet(self.model, self.session, using=self._using)
        new_qs._query = query
        return new_qs

    def offset(self, count: int) -> QuerySet[ModelType]:
        """
        Offset queryset (Django-like).
        
        Args:
            count: Number of objects to skip
        
        Returns:
            New QuerySet with offset applied
        
        Example:
            users = await User.objects.offset(10).limit(10)  # Pagination
        """
        query = self._get_query().offset(count)
        new_qs = QuerySet(self.model, self.session, using=self._using)
        new_qs._query = query
        return new_qs

    async def values(self, *fields: str) -> list[dict[str, Any]]:
        """
        Return values as dictionaries (Django-like).
        
        Args:
            *fields: Field names to include (if empty, all fields)
        
        Returns:
            List of dictionaries
        
        Example:
            users = await User.objects(session).values("email", "is_active")
        """
        base_query = self._get_query()
        
        if fields:
            # Select specific fields
            selected_fields = [getattr(self.model, field) for field in fields if hasattr(self.model, field)]
            # Apply where clause from base query
            query = select(*selected_fields)
            if hasattr(base_query, "whereclause") and base_query.whereclause is not None:
                query = query.where(base_query.whereclause)
        else:
            # Select all fields (use base query)
            query = base_query

        result = await self.session.execute(query)
        rows = result.all()

        if fields:
            return [dict(zip(fields, row)) for row in rows]
        else:
            # Convert model instances to dicts
            instances = [row[0] if isinstance(row, tuple) else row for row in rows]
            return [{c.name: getattr(inst, c.name) for c in self.model.__table__.columns} for inst in instances]

    async def values_list(self, *fields: str, flat: bool = False) -> list[Any]:
        """
        Return values as tuples or flat list (Django-like).
        
        Args:
            *fields: Field names to include
            flat: If True and only one field, return flat list
        
        Returns:
            List of tuples or flat list
        
        Example:
            emails = await User.objects(session).values_list("email", flat=True)
        """
        if not fields:
            raise ValueError("values_list() must be called with at least one field")

        base_query = self._get_query()
        selected_fields = [getattr(self.model, field) for field in fields if hasattr(self.model, field)]
        query = select(*selected_fields)
        
        # Apply where clause from base query
        if hasattr(base_query, "whereclause") and base_query.whereclause is not None:
            query = query.where(base_query.whereclause)

        result = await self.session.execute(query)
        rows = result.all()

        if flat and len(fields) == 1:
            return [row[0] for row in rows]
        else:
            return [tuple(row) for row in rows]

    def distinct(self) -> QuerySet[ModelType]:
        """
        Return distinct objects (Django-like).
        
        Returns:
            New QuerySet with distinct applied
        
        Example:
            users = await User.objects(session).distinct().all()
        """
        query = self._get_query().distinct()
        new_qs = QuerySet(self.model, self.session, using=self._using)
        new_qs._query = query
        return new_qs

    async def delete(self) -> int:
        """
        Delete objects (Django-like).
        
        Returns:
            Number of objects deleted
        
        Example:
            deleted = await User.objects(session).filter(is_active=False).delete()
        """
        query = self._get_query()
        # Get all matching objects first
        result = await self.session.execute(query)
        instances = list(result.scalars().all())
        
        # Delete each instance (triggers signals)
        for instance in instances:
            await self.session.delete(instance)
        
        await self.session.commit()
        return len(instances)

    async def update(self, **kwargs: Any) -> int:
        """
        Update objects (Django-like).
        
        Args:
            **kwargs: Field values to update
        
        Returns:
            Number of objects updated
        
        Example:
            updated = await User.objects(session).filter(is_active=False).update(is_active=True)
        """
        query = self._get_query()
        # Build where clause from query
        where_clause = query.whereclause if hasattr(query, "whereclause") and query.whereclause is not None else True
        
        update_stmt = update(self.model).where(where_clause).values(**kwargs)
        result = await self.session.execute(update_stmt)
        await self.session.commit()
        return result.rowcount

    async def bulk_create(
        self,
        objects: list[ModelType],
        *,
        batch_size: Optional[int] = None,
    ) -> list[ModelType]:
        """
        Bulk create objects (Django-like).
        
        Args:
            objects: List of model instances to create
            batch_size: Optional batch size for bulk insert
        
        Returns:
            List of created instances
        
        Example:
            users = await User.objects.bulk_create(session, [User(email="1@x.com"), User(email="2@x.com")])
        """
        self.session.add_all(objects)
        await self.session.flush()
        await self.session.commit()
        return objects

    async def bulk_update(
        self,
        objects: list[ModelType],
        fields: list[str],
        *,
        batch_size: Optional[int] = None,
    ) -> None:
        """
        Bulk update objects (Django-like).
        
        Args:
            objects: List of model instances to update
            fields: List of field names to update
            batch_size: Optional batch size for bulk update
        
        Example:
            await User.objects.bulk_update(session, users, ["is_active", "is_staff"])
        """
        for obj in objects:
            self.session.add(obj)
        await self.session.flush()
        await self.session.commit()

    async def __aiter__(self):
        """Async iterator support."""
        query = self._get_query()
        result = await self.session.stream(query)
        async for row in result:
            yield row.scalar_one()


class Manager:
    """
    Django-like Manager for models.
    
    Provides the QuerySet interface: Model.objects.filter(), Model.objects.get(), etc.
    """

    def __init__(self, model: type[ModelType]):
        self.model = model

    def __call__(self, session: AsyncSession) -> QuerySet[ModelType]:
        """
        Create a QuerySet for the given session.
        
        Args:
            session: Async database session
        
        Returns:
            QuerySet instance
        
        Example:
            qs = User.objects(session)
            users = await qs.filter(is_active=True).all()
        """
        return QuerySet(self.model, session)
    
    def using(self, db_alias: str) -> "Manager[ModelType]":
        """
        Select database to use (Django-like).
        
        Args:
            db_alias: Database alias (e.g., "default", "analytics")
        
        Returns:
            Manager configured to use the specified database
        
        Note: This returns a manager that will use the specified database
        when creating sessions. You still need to pass a session from that database.
        
        Example:
            from project.core.db.session import get_sessionmaker
            sessionmaker = get_sessionmaker("analytics")
            async with sessionmaker() as session:
                users = await User.objects.using("analytics").all(session)
        """
        # Create a new manager instance with database routing
        manager = Manager(self.model)
        manager._using = db_alias
        return manager

    async def all(self, session: AsyncSession) -> list[ModelType]:
        """Get all objects."""
        return await QuerySet(self.model, session).all()

    async def filter(self, session: AsyncSession, **kwargs: Any) -> list[ModelType]:
        """Filter objects."""
        qs = QuerySet(self.model, session)
        return await qs.filter(**kwargs).all()

    async def exclude(self, session: AsyncSession, **kwargs: Any) -> list[ModelType]:
        """Exclude objects."""
        qs = QuerySet(self.model, session)
        return await qs.exclude(**kwargs).all()

    async def get(self, session: AsyncSession, **kwargs: Any) -> ModelType:
        """Get single object."""
        return await QuerySet(self.model, session).get(**kwargs)

    async def first(self, session: AsyncSession, **kwargs: Any) -> Optional[ModelType]:
        """Get first object."""
        qs = QuerySet(self.model, session)
        if kwargs:
            qs = await qs.filter(**kwargs)
        return await qs.first()

    async def last(self, session: AsyncSession, **kwargs: Any) -> Optional[ModelType]:
        """Get last object."""
        qs = QuerySet(self.model, session)
        if kwargs:
            qs = await qs.filter(**kwargs)
        return await qs.last()

    async def count(self, session: AsyncSession, **kwargs: Any) -> int:
        """Count objects."""
        qs = QuerySet(self.model, session)
        if kwargs:
            qs = await qs.filter(**kwargs)
        return await qs.count()

    async def exists(self, session: AsyncSession, **kwargs: Any) -> bool:
        """Check if objects exist."""
        return await QuerySet(self.model, session).exists(**kwargs)

    async def create(self, session: AsyncSession, **kwargs: Any) -> ModelType:
        """Create and save a new instance."""
        instance = self.model(**kwargs)
        await instance.save(session)
        return instance

    async def get_or_create(
        self,
        session: AsyncSession,
        defaults: Optional[dict[str, Any]] = None,
        **lookup: Any,
    ) -> tuple[ModelType, bool]:
        """Get existing or create new."""
        return await self.model.get_or_create(session, defaults=defaults, **lookup)

    async def update_or_create(
        self,
        session: AsyncSession,
        defaults: Optional[dict[str, Any]] = None,
        **lookup: Any,
    ) -> tuple[ModelType, bool]:
        """Update existing or create new."""
        return await self.model.update_or_create(session, defaults=defaults, **lookup)

    async def bulk_create(
        self,
        session: AsyncSession,
        objects: list[ModelType],
        *,
        batch_size: Optional[int] = None,
    ) -> list[ModelType]:
        """Bulk create objects."""
        return await QuerySet(self.model, session).bulk_create(objects, batch_size=batch_size)

    async def bulk_update(
        self,
        session: AsyncSession,
        objects: list[ModelType],
        fields: list[str],
        *,
        batch_size: Optional[int] = None,
    ) -> None:
        """Bulk update objects."""
        await QuerySet(self.model, session).bulk_update(objects, fields, batch_size=batch_size)


class DoesNotExist(Exception):
    """Exception raised when get() finds no objects."""

    pass


class MultipleObjectsReturned(Exception):
    """Exception raised when get() finds multiple objects."""

    pass


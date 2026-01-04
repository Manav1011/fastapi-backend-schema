from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import DeclarativeBase

from project.core.db.methods import ModelMethodsMixin
from project.core.db.queryset import Manager


class Base(DeclarativeBase, ModelMethodsMixin):
    """
    Base class for all models.
    
    Provides Django-like methods: save(), delete(), refresh(), update(),
    create(), get_or_create(), update_or_create()
    
    Also integrates with signals: pre_save, post_save, pre_delete, post_delete
    
    Django-like QuerySet access via .objects:
        users = await User.objects.all(session)
        user = await User.objects.get(session, email="test@example.com")
        active_users = await User.objects.filter(session, is_active=True)
    
    Django-like __str__ method:
        Override __str__ in your model to customize string representation.
        Default tries common fields: name, title, email, username, slug
    
    Django-like database routing:
        # Specify database for a model:
        class MyModel(Base):
            _database = "analytics"  # Use "analytics" database
        
        # Or use 'using' parameter in queries:
        users = await User.objects.using("analytics").all(session)
    """
    
    # Django-like manager
    objects: Manager = Manager(None)  # Will be set per model class
    
    # Database routing (Django-like)
    # Set this in your model to specify which database to use
    # Example: _database = "analytics"
    _database: Optional[str] = None
    
    def __init_subclass__(cls, **kwargs):
        """Set up objects manager for each model class."""
        super().__init_subclass__(**kwargs)
        cls.objects = Manager(cls)
    
    def __str__(self) -> str:
        """
        Django-like string representation.
        
        Tries common fields in order: name, title, email, username, slug
        Falls back to class name + primary key if none found.
        
        Override in your model to customize:
            def __str__(self):
                return f"{self.name} ({self.id})"
        """
        # Try common field names (Django-like)
        for field_name in ["name", "title", "email", "username", "slug"]:
            if hasattr(self, field_name):
                value = getattr(self, field_name)
                if value is not None:
                    return str(value)
        
        # Fallback: use primary key
        pk = self.__table__.primary_key
        if pk:
            pk_value = getattr(self, pk.columns[0].name, None)
            if pk_value is not None:
                return f"{self.__class__.__name__}({pk_value})"
        
        # Last resort: class name
        return f"{self.__class__.__name__} object"
    
    def __repr__(self) -> str:
        """
        Representation for debugging (uses __str__ by default).
        
        Override if you need different repr vs str.
        """
        return self.__str__()



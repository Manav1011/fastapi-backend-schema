"""Database utilities and Django-like helpers."""

from project.core.db.base import Base
from project.core.db.fields import (
    CASCADE,
    DO_NOTHING,
    PROTECT,
    SET_DEFAULT,
    SET_NULL,
    create_foreign_key,
    create_many_to_many,
    create_one_to_one,
    create_relationship,
)
from project.core.db.mixins import (
    DescriptionMixin,
    IntegerPrimaryKeyMixin,
    NameMixin,
    SlugMixin,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from project.core.db.queryset import (
    DoesNotExist,
    Manager,
    MultipleObjectsReturned,
    QuerySet,
)
from project.core.db.session import (
    get_async_session,
    get_default_engine,
    get_default_sessionmaker,
    get_engine,
    get_sessionmaker,
)
from project.core.db.routing import DatabaseRouter, get_db_for_model
from project.core.db.signals import (
    m2m_changed,
    post_delete,
    post_init,
    post_save,
    pre_delete,
    pre_init,
    pre_save,
)

__all__ = [
    # Base
    "Base",
    # Session utilities
    "get_async_session",
    "get_engine",
    "get_sessionmaker",
    "get_default_engine",
    "get_default_sessionmaker",
    # Database routing (Django-like)
    "DatabaseRouter",
    "get_db_for_model",
    # QuerySet (Django-like)
    "QuerySet",
    "Manager",
    "DoesNotExist",
    "MultipleObjectsReturned",
    # Field helpers (Django-like)
    "create_foreign_key",
    "create_relationship",
    "create_many_to_many",
    "create_one_to_one",
    # on_delete constants
    "CASCADE",
    "PROTECT",
    "SET_NULL",
    "SET_DEFAULT",
    "DO_NOTHING",
    # Mixins
    "TimestampMixin",
    "SoftDeleteMixin",
    "UUIDPrimaryKeyMixin",
    "IntegerPrimaryKeyMixin",
    "NameMixin",
    "SlugMixin",
    "DescriptionMixin",
    # Signals (Django-like)
    "pre_save",
    "post_save",
    "pre_delete",
    "post_delete",
    "pre_init",
    "post_init",
    "m2m_changed",
]

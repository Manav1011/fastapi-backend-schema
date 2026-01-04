from __future__ import annotations

import json
import uuid
from datetime import date, datetime, time
from typing import Any, Optional

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession

from project.core.db.base import Base


class DatabaseEncoder(json.JSONEncoder):
    """JSON encoder for database models."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, (datetime, date, time)):
            return obj.isoformat()
        if isinstance(obj, bytes):
            return obj.decode("utf-8", errors="ignore")
        return super().default(obj)


def model_to_dict(instance: Base) -> dict[str, Any]:
    """Convert a model instance to a dictionary for serialization."""
    mapper = inspect(instance.__class__)
    fields = {}
    
    # Get primary key
    pk_columns = mapper.primary_key
    pk = getattr(instance, pk_columns[0].name) if pk_columns else None
    if isinstance(pk, uuid.UUID):
        pk = str(pk)

    # Get all other columns
    for column in mapper.columns:
        if column not in pk_columns:
            fields[column.name] = getattr(instance, column.name)
    
    return {
        "model": f"{instance.__class__.__module__.replace('.models', '')}.{instance.__class__.__name__}",
        "pk": pk,
        "fields": fields,
    }


async def dump_data(
    session: AsyncSession,
    models: list[type[Base]],
) -> str:
    """Dump data from models to a JSON string."""
    data = []
    for model in models:
        result = await session.execute(model.objects(session)._get_query())
        instances = result.scalars().all()
        for instance in instances:
            data.append(model_to_dict(instance))
    
    return json.dumps(data, cls=DatabaseEncoder, indent=2)


async def load_data(
    session: AsyncSession,
    data: list[dict[str, Any]],
    registry_models: dict[str, type[Base]],
) -> int:
    """Load data from a list of dicts into the database."""
    count = 0
    for entry in data:
        model_path = entry["model"]
        pk = entry["pk"]
        fields = entry["fields"]
        
        # Split project.apps.users.User -> project.apps.users, User
        # The registry usually stores by name or path.
        # Let's try to find it in the registry_models
        model_name = model_path.split(".")[-1]
        model_cls = registry_models.get(model_name)
        
        if not model_cls:
            # Try to match by full path if possible
            for name, cls in registry_models.items():
                full_path = f"{cls.__module__.replace('.models', '')}.{cls.__name__}"
                if full_path == model_path:
                    model_cls = cls
                    break
        
        if not model_cls:
            raise ValueError(f"Model {model_path} not found in registry")
        
        # Handle types (UUID, datetime)
        from sqlalchemy import types
        for key, value in fields.items():
            column = model_cls.__table__.columns.get(key)
            if column is not None and isinstance(value, str):
                if isinstance(column.type, (types.DateTime, types.Date, types.Time)):
                    try:
                        fields[key] = datetime.fromisoformat(value)
                    except ValueError:
                        pass
                elif "GUID" in str(column.type) or "UUID" in str(column.type):
                    try:
                        fields[key] = uuid.UUID(value)
                    except ValueError:
                        pass

        # Use update_or_create logic
        pk_name = model_cls.__table__.primary_key.columns[0].name
        
        # Convert pk to proper type if needed
        if "GUID" in str(model_cls.__table__.columns[pk_name].type) and isinstance(pk, str):
            pk = uuid.UUID(pk)
            
        lookup = {pk_name: pk}
        await model_cls.update_or_create(session, defaults=fields, **lookup)
        count += 1
    
    await session.commit()
    return count

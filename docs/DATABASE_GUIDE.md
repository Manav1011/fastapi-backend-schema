# 🗄️ Database Management Guide

This project supports a Django-like multi-database architecture using SQLAlchemy as the ORM. You can configure multiple databases, different engines (SQLite, PostgreSQL, MySQL), and control where your models store their data.

---

## ⚙️ 1. Configuration (`.env`)

Databases are defined in your `.env` file. You can use a single `DATABASE_URL` for simple projects or a `DATABASES` string for multi-db setups.

### Single Database (Default)
```bash
DATABASE_URL=sqlite+aiosqlite:///./db.sqlite3
```

### Multiple Databases
Format: `alias1:url1,alias2:url2`
```bash
DATABASES=default:sqlite+aiosqlite:///./db.sqlite3,analytics:postgresql+asyncpg://user:pass@localhost/analytics_db
```

**Supported Protocols:**
- **SQLite**: `sqlite+aiosqlite:///filename.db`
- **PostgreSQL**: `postgresql+asyncpg://user:pass@host/dbname`
- **MySQL**: `mysql+aiomysql://user:pass@host/dbname`

---

## 🏗️ 2. How to Access Databases

### In Views (Automatic Injection)
The `get_async_session` dependency always uses the **`default`** database unless specified otherwise.

```python
from project.core.db import get_async_session

@router.get("/")
async def list_data(session: AsyncSession = Depends(get_async_session)):
    # Uses the default database
    results = await MyModel.objects.all(session)
```

### In Services or Scripts (Manual Session)
Use the `get_sessionmaker` utility to access specific databases manually.

```python
from project.core.db import get_sessionmaker

# Get sessionmaker for a specific alias
analytics_sm = get_sessionmaker("analytics")

async with analytics_sm() as session:
    # This query runs against the analytics database
    logs = await EventLog.objects.all(session)
```

---

## 🎯 3. Routing Models to Specific Databases

You can hardcode a model to always use a specific database by setting the `__database__` attribute on the model class.

```python
from project.core.db import Base

class AnalyticsLog(Base):
    __tablename__ = "analytics_logs"
    __database__ = "analytics"  # Always routes queries for this model to 'analytics' db
    
    # ... fields
```

---

## 🛠️ 4. Using the Django-like ORM

The project uses a custom Manager (`.objects`) and Model methods to make operations intuitive.

| Operation | Syntax |
|-----------|--------|
| **Fetch All** | `await Model.objects.all(session)` |
| **Filter** | `await Model.objects.filter(session, status="active").all()` |
| **Get Single** | `await Model.objects.get(session, id=1)` |
| **Create** | `await Model.create(session, **data)` |
| **Update** | `await instance.update(session, **data)` |
| **Delete** | `await instance.delete(session)` |
| **Get or Create** | `obj, created = await Model.get_or_create(session, defaults={...}, name="test")` |

---

## 🔄 5. Migrations with Multiple DBs

When running migrations, the system automatically detects all models across all installed apps.

1. **Generate**: `python manage.py makemigrations -m "add analytics"`
2. **Apply**: `python manage.py migrate`

*Note: For complex multi-db migration routing, refer to the custom Alembic environment logic in `alembic/env.py`.*

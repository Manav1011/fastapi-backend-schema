# FastAPI Backend - Django-like Architecture

A production-ready FastAPI backend framework that brings Django's developer experience to the async world of FastAPI, SQLAlchemy, and modern Python.

## 🎯 Why This Architecture?

Django is beloved for its **developer experience** - the `manage.py` commands, app-based structure, automatic discovery, and intuitive ORM. However, Django's synchronous nature limits performance for modern async workloads.

This architecture combines:
- **Django's developer experience** - Familiar patterns, commands, and structure
- **FastAPI's performance** - Async-first, type-safe, auto-generated API docs
- **SQLAlchemy's flexibility** - Powerful ORM with async support
- **Modern Python** - Type hints, async/await, Pydantic validation

## ✨ Key Features

### 🏗️ Django-like Architecture

- **`manage.py`** - Django-style CLI for all operations
- **`settings.py`** - Centralized configuration with environment variables
- **App-based structure** - Modular, reusable apps with autodiscovery
- **`INSTALLED_APPS`** - Automatic model, router, and admin registration
- **Multiple database support** - Django-like `DATABASES` dictionary

### 🔧 Django-like ORM

- **`.objects` manager** - `User.objects.all()`, `User.objects.filter()`, etc.
- **Django-like methods** - `save()`, `delete()`, `create()`, `get_or_create()`, `update_or_create()`
- **QuerySet chaining** - `filter()`, `exclude()`, `order_by()`, `limit()`, `offset()`
- **`__str__` method** - Automatic string representation for models
- **Database routing** - Specify database per model or query

### 🚀 FastAPI Features

- **Async-first** - All database operations are async
- **Type safety** - Full type hints with Pydantic validation
- **Auto API docs** - Swagger/ReDoc automatically generated
- **High performance** - Built on Starlette and Pydantic
- **Modern Python** - Python 3.10+ features

### 🛠️ Developer Tools

- **`python manage.py shell`** - Interactive shell with pre-loaded models
- **`python manage.py createsuperuser`** - Create admin users
- **`python manage.py createapp`** - Generate app boilerplate
- **`python manage.py makemigrations`** - Create database migrations
- **`python manage.py migrate`** - Apply migrations
- **`python manage.py runserver`** - Start development server

### 🔐 Built-in Features

- **JWT Authentication** - FastAPI Users integration
- **Admin Panel** - SQLAdmin with auto-registration
- **Signals System** - Django-like `pre_save`, `post_save`, `pre_delete`, etc.
- **Consistent API Responses** - Standardized response format
- **Middleware Stack** - CORS, trusted hosts, request ID, access logs, GZip
- **Error Handling** - Consistent error responses
- **Multiple Databases** - Support for SQLite, PostgreSQL, MySQL

## 📁 Project Structure

```
fastapi-backend/
├── manage.py                 # Django-like CLI
├── alembic/                  # Database migrations
│   ├── env.py
│   └── versions/
├── project/                  # Main project module
│   ├── main.py              # FastAPI app factory
│   ├── settings.py          # Configuration (Django-like)
│   ├── api/                  # API routing
│   │   └── v1.py
│   ├── apps/                 # Django-like apps
│   │   └── users/           # User app (built-in)
│   │       ├── models.py
│   │       ├── urls.py
│   │       ├── views.py
│   │       ├── schemas.py
│   │       ├── service.py       # Business logic
│   │       └── admin.py
│   └── core/                 # Core utilities
│       ├── db/              # Database utilities
│       │   ├── base.py      # Base model class
│       │   ├── queryset.py  # Django-like QuerySet
│       │   ├── methods.py   # save(), delete(), etc.
│       │   ├── session.py   # Database sessions
│       │   ├── signals.py   # Django-like signals
│       │   └── routing.py   # Database routing
│       ├── registry.py      # App autodiscovery
│       ├── admin/           # Admin panel
│       └── middleware/      # Custom middleware
└── requirements.txt
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd fastapi-backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp env.example .env

# Edit .env and set your configuration
# - SECRET_KEY (generate a secure random string)
# - JWT_SECRET (generate a secure random string)
# - DATABASE_URL or DATABASES (for multiple databases)
```

### 3. Database Setup

```bash
# Create migrations
python manage.py makemigrations -m "initial"

# Apply migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser
```

### 4. Run Server

```bash
# Start development server
python manage.py runserver --reload

# Server runs at http://127.0.0.1:8000
# API docs at http://127.0.0.1:8000/api/v1/docs
# Admin panel at http://127.0.0.1:8000/admin
```

## 📖 Usage Examples

### Creating a New App

```bash
python manage.py createapp blog
```

This creates:
```
project/apps/blog/
├── __init__.py
├── models.py      # Define your models
├── schemas.py     # Request/response schemas
├── views.py       # View functions
├── service.py     # Business logic & data access
├── urls.py        # Router definition
└── admin.py       # Admin registrations
```

### Defining Models

```python
from project.core.db import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text

class Post(Base):
    __tablename__ = "posts"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    
    def __str__(self) -> str:
        return self.title
```

### Using the ORM (Django-like)

```python
from project.core.db.session import get_sessionmaker
from project.apps.blog.models import Post

# Get sessionmaker
sessionmaker = get_sessionmaker()

# Query (Django-like)
async with sessionmaker() as session:
    # Get all
    posts = await Post.objects.all(session)
    
    # Filter
    published = await Post.objects.filter(session, is_published=True).all()
    
    # Get single
    post = await Post.objects.get(session, id=1)
    
    # Create
    new_post = await Post.create(session, title="Hello", content="World")
    
    # Update
    await post.update(session, title="Updated Title")
    
    # Delete
    await post.delete(session)
```

### Multiple Databases

```python
# .env
DATABASES=default:sqlite+aiosqlite:///./db.sqlite3,analytics:postgresql+asyncpg://user:pass@localhost/analytics

# Usage
from project.core.db.session import get_sessionmaker

# Default database
default_sm = get_sessionmaker("default")
async with default_sm() as session:
    users = await User.objects.all(session)

# Analytics database
analytics_sm = get_sessionmaker("analytics")
async with analytics_sm() as session:
    events = await AnalyticsEvent.objects.all(session)
```

### Creating Views

```python
# project/apps/blog/views.py
from fastapi import Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from project.core.db import get_async_session
from project.core.responses import BaseResponse
from .urls import router
from .schemas import PostListResponse, PostRead
from . import service

@router.get("/", response_model=PostListResponse, status_code=status.HTTP_200_OK)
async def list_posts(
    session: AsyncSession = Depends(get_async_session)
) -> PostListResponse:
    """List all posts."""
    posts = await service.get_all_posts(session)
    return PostListResponse(
        success=True,
        status_code=status.HTTP_200_OK,
        message="Posts retrieved successfully",
        data=[PostRead(id=p.id, title=p.title) for p in posts],
    )
```

## 🆚 How It's Better Than Django

### 1. **Performance**
- **Async-first**: All database operations are async, enabling true concurrency
- **FastAPI**: Built on Starlette, one of the fastest Python frameworks
- **No GIL limitations**: Async I/O doesn't block on database queries

### 2. **Type Safety**
- **Full type hints**: Every function, model, and schema is typed
- **Pydantic validation**: Automatic request/response validation
- **IDE support**: Better autocomplete and error detection

### 3. **API-First**
- **Auto-generated docs**: Swagger/ReDoc automatically generated
- **OpenAPI standard**: Industry-standard API documentation
- **Modern API design**: RESTful by default, easy to extend

### 4. **Modern Python**
- **Python 3.10+**: Uses latest Python features
- **Async/await**: Native async support throughout
- **Type hints**: Full type coverage

### 5. **Flexibility**
- **SQLAlchemy**: More powerful ORM than Django ORM
- **Multiple databases**: Easy to use different databases per model
- **No magic**: Explicit is better than implicit

### 6. **Developer Experience**
- **Same as Django**: Familiar commands and patterns
- **Better tooling**: Type hints, async shell, better error messages
- **Modern stack**: Uses latest libraries and patterns

## 🎨 Django Features Implemented

| Django Feature | Implementation | Status |
|----------------|----------------|--------|
| `manage.py` | ✅ Full CLI with all commands | Complete |
| `settings.py` | ✅ Centralized configuration | Complete |
| `INSTALLED_APPS` | ✅ App autodiscovery | Complete |
| `.objects` manager | ✅ Django-like QuerySet | Complete |
| `save()`, `delete()` | ✅ Model methods | Complete |
| `get_or_create()` | ✅ QuerySet methods | Complete |
| Signals | ✅ `pre_save`, `post_save`, etc. | Complete |
| Admin panel | ✅ SQLAdmin integration | Complete |
| Migrations | ✅ Alembic integration | Complete |
| Multiple databases | ✅ `DATABASES` dictionary | Complete |
| `__str__` method | ✅ Automatic representation | Complete |
| App structure | ✅ Modular apps | Complete |
| Shell | ✅ Interactive shell | Complete |

## 🔧 Configuration

### Environment Variables

```bash
# Basic
ENV=local
DEBUG=true
SECRET_KEY=your-secret-key-here

# Database (single)
DATABASE_URL=sqlite+aiosqlite:///./db.sqlite3

# Database (multiple)
DATABASES=default:sqlite+aiosqlite:///./db.sqlite3,analytics:postgresql+asyncpg://user:pass@localhost/analytics

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Admin
ADMIN_PATH=/admin

# JWT
JWT_SECRET=your-jwt-secret-here
JWT_LIFETIME_SECONDS=3600
```

## 📚 Available Commands

```bash
# Start server
python manage.py runserver [--host HOST] [--port PORT] [--reload]

# Database migrations
python manage.py makemigrations [-m MESSAGE]
python manage.py migrate [--revision REVISION]

# User management
python manage.py createsuperuser

# Development
python manage.py shell

# App creation
python manage.py createapp NAME [--add-to-installed]
```

## 🏛️ Architecture Decisions

### Why FastAPI over Django?
- **Async performance**: True async/await support
- **Type safety**: Full type hints and validation
- **API-first**: Built for modern API development
- **Performance**: 2-3x faster than Django for API workloads

### Why SQLAlchemy over Django ORM?
- **More powerful**: Supports complex queries and relationships
- **Async support**: Native async/await support
- **Flexibility**: Can use raw SQL when needed
- **Industry standard**: Widely used in Python ecosystem

### Why This Structure?
- **Familiar**: Django developers feel at home
- **Modular**: Apps are self-contained and reusable
- **Scalable**: Easy to add new apps and features
- **Maintainable**: Clear separation of concerns

## 🧪 Testing

```bash
# Run tests (when implemented)
pytest

# With coverage
pytest --cov=project
```

## 📦 Dependencies

- **FastAPI** - Web framework
- **SQLAlchemy** - ORM with async support
- **Alembic** - Database migrations
- **FastAPI Users** - Authentication
- **SQLAdmin** - Admin panel
- **Pydantic** - Data validation
- **Typer** - CLI framework
- **Uvicorn** - ASGI server

## 🤝 Contributing

This is a boilerplate template. Feel free to:
1. Fork the repository
2. Create your own apps
3. Extend the functionality
4. Share improvements

## 📄 License

MIT License - feel free to use this as a starting point for your projects.

## 🙏 Acknowledgments

- **Django** - For the excellent developer experience patterns
- **FastAPI** - For the modern async framework
- **SQLAlchemy** - For the powerful ORM
- **FastAPI Users** - For authentication utilities

## 🚀 Next Steps

1. **Create your first app**: `python manage.py createapp myapp`
2. **Define models**: Add models in `myapp/models.py`
3. **Create migrations**: `python manage.py makemigrations`
4. **Apply migrations**: `python manage.py migrate`
5. **Build your API**: Add views and routes
6. **Deploy**: Use your favorite deployment platform

---

**Built with ❤️ for developers who love Django's DX but need FastAPI's performance.**


# 🏗️ Core Architecture Guide

The `project/core/` directory is the heart of the application. It contains the foundational logic, utilities, and base classes that power the Django-like experience in FastAPI.

---

## 📁 Folder Structure & File Descriptions

### 🔧 Top-Level Files
- **`__init__.py`**: Makes the directory a package.
- **`logging.py`**: Configures the application's logging system (vibrant console logs and file logging).
- **`registry.py`**: The **Autodiscovery Engine**. It scans `INSTALLED_APPS` to automatically import models, routers, and admin classes.
- **`responses.py`**: Defines the `BaseResponse` and `ErrorResponse` Pydantic models to ensure a consistent JSON envelope for all APIs.
- **`errors.py`**: Contains global exception handlers that catch `ApiError`, validation errors, and crashes to return them in a standardized format.

---

### 🗄️ `core/db/` (Database & ORM)
This is where the Django-like ORM magic happens.

- **`base.py`**: Defines the `Base` class. Every model in the project inherits from this to get `.objects`, `.save()`, and `.delete()`.
- **`queryset.py`**: Implements the `QuerySet` and `Manager` classes. This provides `filter()`, `get()`, `exclude()`, and `all()`.
- **`methods.py`**: A mixin that adds instance methods like `update()`, `refresh()`, and `create()` to your models.
- **`fields.py`**: Helpers for relationships (`create_foreign_key`, `create_relationship`).
- **`mixins.py`**: Pre-built model behaviors like `TimestampMixin` (created_at/updated_at) and `SoftDeleteMixin`.
- **`signals.py`**: An async signal dispatcher allowing you to hook into `pre_save`, `post_save`, etc.
- **`session.py`**: Manages SQLAlchemy engines and async session factories.
- **`routing.py`**: Handles multi-database routing (deciding which DB to use for a model).
- **`serialization.py`**: Powering `dumpdata` and `loaddata` by converting models to/from JSON.

---

### 🛡️ `core/middleware/` (Request Processing)
- **`request_id.py`**: Injects a unique `X-Request-ID` into every request for tracing.
- **`access_log.py`**: Automatically logs the duration and status of every HTTP request.

---

### 🛠️ `core/admin/` (Admin Panel)
- **`site.py`**: Configures the `sqladmin` instance. It provides a centralized `admin_site` where any app can register its `ModelView` (just like `admin.site.register` in Django).

---

## 🚀 Why this structure?
This separation of concerns ensures that the "plumbing" (database setup, error handling, logging) is isolated from your actual business logic. When you create a new app, you interact with these core features through clean, high-level APIs.

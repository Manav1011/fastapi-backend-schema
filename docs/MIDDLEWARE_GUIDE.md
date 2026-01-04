# 🛡️ Middleware Guide

Middlewares are components that run on every request/response cycle. This project uses a mix of standard security middlewares and custom utility middlewares.

---

## 🏗️ 1. Core Middlewares (Included)

These are located in `project/core/middleware/` and are active by default.

### 🆔 Request ID Middleware (`X-Request-ID`)
- **File**: `request_id.py`
- **Function**: Generates a unique UUID for every incoming request.
- **Why**: Allows tracing a specific user's journey through the logs. It attaches the ID to `request.state.request_id` and adds it to the response headers.

### 📝 Access Log Middleware
- **File**: `access_log.py`
- **Function**: Logs the Method, Path, Status Code, and Processing Time (ms) for every request.
- **Why**: Provides real-time visibility into API performance and usage directly in your terminal.

---

## 📦 Standard Middlewares (Settings-Driven)

These are built-in FastAPI/Starlette middlewares that you can control via your `.env` or `settings.py`.

### 🌐 CORS Middleware
- **Control**: `CORS_ORIGINS` in `.env`.
- **Function**: Handles "Cross-Origin Resource Sharing".
- **Usage**: Set this to your frontend URL (e.g., `http://localhost:3000`) to allow your website to talk to your API.

### 🏠 Trusted Host Middleware
- **Control**: `TRUSTED_HOSTS` in `.env`.
- **Function**: Guards against Host Header attacks.
- **Usage**: Set this to your actual domain name in production.

### 🤐 GZip Middleware
- **Control**: Hardcoded to activate for responses > 1KB.
- **Function**: Compresses JSON responses to save bandwidth and speed up mobile users.

---

## ➕ 2. How to Add a New Middleware

### Step 1: Create the file
Create `project/core/middleware/maintenance.py`:

```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

class MaintenanceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Example: Block all requests if a flag is set
        is_maintenance = False 
        if is_maintenance:
            return JSONResponse({"message": "Down for maintenance"}, status_code=503)
        return await call_next(request)
```

### Step 2: Register it
Open `project/main.py` and import/add your middleware in the `create_app()` function:

```python
from project.core.middleware.maintenance import MaintenanceMiddleware

def create_app() -> FastAPI:
    # ...
    app.add_middleware(MaintenanceMiddleware)
    # ...
```

---

## 🚫 3. How to Disable a Middleware

To disable a middleware, simply comment out or remove the `app.add_middleware(...)` line in `project/main.py`.

> **Note on Order**: Middlewares are executed in **reverse order** of registration for the request (the last one added is the first to run) and in **regular order** for the response. Usually, `RequestIdMiddleware` should stay at the top so that the ID is available to all other middlewares (like the logger).

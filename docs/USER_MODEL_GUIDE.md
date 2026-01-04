# 👤 User Model & Authentication Guide

The project provides a fully-featured, production-ready `User` model out of the box, powered by `fastapi-users` and enhanced with Django-like fields.

---

## 🏗️ 1. The User Model (`project/apps/users/models.py`)

The `User` model uses a **UUID** as the primary key and inherits from `SQLAlchemyBaseUserTableUUID`.

### Included Features:
- **ID**: Secure UUID primary key.
- **Authentication**: `email` and `hashed_password`.
- **Status Flags**: 
  - `is_active`: Can the user log in?
  - `is_verified`: Has the user verified their email?
  - `is_superuser`: Total access over the system.
- **Django-like Extensions**:
  - `is_staff`: Can the user access the admin panel?
  - `date_joined`: Automatically set when the user registers.
  - `last_login`: Tracks the last time the user authenticated.

---

## 🔐 2. Authentication System

We use **JWT (JSON Web Tokens)** for stateless authentication.

### Key Components (`project/apps/users/auth.py`):
1. **UserManager**: Handles logic for registering users, password resets, and verification.
2. **JWT Strategy**: Configures the secret key and token expiration (`JWT_LIFETIME_SECONDS`).
3. **Bearer Transport**: Defines how the token is sent (via the `Authorization: Bearer <token>` header).

---

## 🌐 3. Default API Endpoints

The `users` app provides the following endpoints automatically at `/api/v1/auth/`:

| Endpoint | Action |
|----------|--------|
| `POST /jwt/login` | Log in and get a JWT token. |
| `POST /jwt/logout` | Log out (client side). |
| `POST /register` | Create a new account. |
| `POST /forgot-password` | Initiate password recovery. |
| `POST /reset-password` | Set a new password using a token. |
| `GET /users/me` | Get the profile of the logged-in user. |
| `PATCH /users/me` | Update your own profile. |

---

## 🛡️ 4. Using Permissions in Your Views

You can protect your routes by using the built-in dependencies in `project/apps/users/urls.py`.

```python
from project.apps.users.urls import get_current_active_user, get_current_staff_user

# Require any logged in user
@router.get("/protected")
async def secret_data(user: User = Depends(get_current_active_user)):
    return {"message": f"Hello {user.email}"}

# Require Staff (Django-like)
@router.get("/staff-only")
async def staff_data(user: User = Depends(get_current_staff_user)):
    return {"message": "Hello Staff Member"}
```

---

## 🛠️ 5. Management Commands
You can manage users from the command line:

```bash
# Create a superuser (interactive)
python manage.py createsuperuser
```

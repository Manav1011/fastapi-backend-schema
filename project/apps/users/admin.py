from __future__ import annotations

from sqladmin import ModelView

from project.core.admin.site import admin_site

# Django-like relative import (same app)
from .models import User


class UserAdmin(ModelView, model=User):
    """Admin view for User model."""

    # Display columns
    column_list = [User.id, User.email, User.is_active, User.is_staff, User.is_superuser, User.date_joined]
    
    # Use __str__ for display (Django-like)
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-user"
    
    # Search and sort
    column_searchable_list = [User.email]
    column_sortable_list = [User.email, User.date_joined]
    
    # Permissions
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    
    # Customize display format
    column_formatters = {
        User.email: lambda m, a: m.email or f"User({m.id})",
    }


# Django-like registration: just register with admin_site
admin_site.register(UserAdmin)

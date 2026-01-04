# 🛠️ Admin Panel Guide

This project includes a powerful, Django-like admin interface powered by **`sqladmin`**. It allows you to manage your database data through a beautiful web dashboard.

---

## 🚀 1. Accessing the Admin
1. Start the server: `python manage.py runserver`
2. Open your browser to: **`http://127.0.0.1:8000/admin/`**

> **Security Note**: By default, only users with `is_staff=True` or `is_superuser=True` can access the admin panel. Use `python manage.py createsuperuser` to create your first admin account.

---

## 📝 2. Registering Your Models

Registration is simple and follows the Django pattern. You define a `ModelView` in your app's `admin.py`.

### Example: `project/apps/blog/admin.py`
```python
from sqladmin import ModelView
from project.core.admin.site import admin_site
from .models import Post

class PostAdmin(ModelView, model=Post):
    name = "Post"
    name_plural = "Posts"
    icon = "fa-solid fa-blog"
    
    # What columns to show in the list view
    column_list = [Post.id, Post.title, Post.created_at]
    
    # Enable search for specific fields
    column_searchable_list = [Post.title]
    
    # Enable sorting
    column_sortable_list = [Post.created_at]

# Register with the global admin site
admin_site.register(PostAdmin)
```

---

## 🎨 3. Key Customization Options

| Property | Description |
|----------|-------------|
| `column_list` | List of fields to show in the main table. |
| `column_details_list` | List of fields to show in the single-item view. |
| `form_columns` | Fields that should appear in the Create/Edit forms. |
| `column_labels` | Rename column headers (e.g., `{Post.title: "Blog Title"}`). |
| `column_formatters` | Logic to format values (e.g., dates or currency). |
| `icon` | FontAwesome icon class (e.g., `fa-solid fa-user`). |

---

## 🧱 4. How it Works (Under the Hood)
1. Individual apps register their `ModelView` classes with the `admin_site` in `project/core/admin/site.py`.
2. When the main FastAPI app starts, the `project.core.registry` autodiscovery imports all `admin.py` files.
3. The `mount_admin` function then attaches `sqladmin` to the FastAPI instance and registers all collected views.

This keeps your code clean: you define the admin interface **inside** the app it belongs to, but it all shows up in one central dashboard.

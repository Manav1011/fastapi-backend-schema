# 🏗️ Model & ORM Guide

This project uses **SQLAlchemy 2.0** with an async-first approach, wrapped in a **Django-like API** to make common operations intuitive and clean.

---

## 📐 1. Defining Models

All models must inherit from `project.core.db.Base`. We use the **Mapped** and **mapped_column** syntax for full type safety.

### Basic Fields
```python
from project.core.db import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text, Boolean, Integer

class Profile(Base):
    __tablename__ = "profiles"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    bio: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
```

---

## 🔗 2. Relationships

Relationships are defined using `Mapped` with the related class and the `relationship()` function.

### One-to-Many (ForeignKey)
```python
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    
    # One Category has Many Posts
    posts: Mapped[list["Post"]] = relationship(back_populates="category")

class Post(Base):
    __tablename__ = "posts"
    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    
    # Many Posts belong to One Category
    category: Mapped["Category"] = relationship(back_populates="posts")
```

### Many-to-Many
Many-to-Many requires an "Association Table".

```python
from sqlalchemy import Table, Column, ForeignKey

# Association Table
post_tags = Table(
    "post_tags",
    Base.metadata,
    Column("post_id", ForeignKey("posts.id"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True),
)

class Tag(Base):
    __tablename__ = "tags"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    
    posts: Mapped[list["Post"]] = relationship(
        secondary=post_tags, back_populates="tags"
    )

class Post(Base):
    # ... other fields
    tags: Mapped[list["Tag"]] = relationship(
        secondary=post_tags, back_populates="posts"
    )
```

---

## 🚀 3. How the ORM Works

We use a custom `Manager` pattern (`.objects`) to make querying feel like Django.

### Basic Queries
```python
# Create
user = await User.create(session, email="test@ex.com", password="...")

# Get by PK
user = await User.objects.get(session, id=1)

# Filter (Multiple)
active_users = await User.objects.filter(session, is_active=True).all()

# Filter (Single)
user = await User.objects.filter(session, email="test@ex.com").first()

# Chaining
results = await User.objects.filter(is_active=True).order_by("-id").limit(10).all(session)
```

### Advanced Operations
- **`get_or_create`**: Finds an object or creates it if it doesn't exist.
  ```python
  tag, created = await Tag.get_or_create(session, name="Technology")
  ```
- **`update_or_create`**: Updates if found, creates if not.
  ```python
  user, created = await User.update_or_create(
      session, email="test@ex.com", defaults={"is_active": False}
  )
  ```

---

## 🔄 4. Saving and Deleting

Unlike standard SQLAlchemy where you have to call `session.add(obj)`, our models have built-in helper methods.

```python
# Update an instance
await user.update(session, is_active=False)

# Delete an instance
await user.delete(session)

# Standard Save (Manual)
user.is_active = True
await session.commit()
```

---

## ⚡ 5. Eager Loading (Joining)

Since we are in an **async** environment, SQLAlchemy does not support lazy loading by default (to avoid accidental blocking I/O). You must explicitly load relationships.

```python
from sqlalchemy.orm import selectinload

# Load posts along with their categories in one query
posts = await Post.objects.all(session, options=[selectinload(Post.category)])

for post in posts:
    print(post.category.name) # Safe to access because it's loaded
```

---

## 🛠️ Summary of ORM Syntax vs Django
| Action | Django | This Project |
|--------|--------|--------------|
| Create | `User.objects.create(...)` | `await User.create(session, ...)` |
| List All | `User.objects.all()` | `await User.objects.all(session)` |
| Filter | `User.objects.filter(k=v)` | `await User.objects.filter(session, k=v).all()` |
| Get One | `User.objects.get(id=1)` | `await User.objects.get(session, id=1)` |
| Delete | `obj.delete()` | `await obj.delete(session)` |

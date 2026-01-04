# 🛠️ Development Guide: Creating Apps & APIs

This document explains the standard workflow for adding new functionality to this project, following its Django-inspired architecture.

---

## 🏗️ 1. Create a New App

Use the management command to generate the app boilerplate. This automatically creates the folder structure and adds the app to `INSTALLED_APPS`.

```bash
python manage.py createapp --name blog
```

**What this creates:**
- `models.py`: Database models (SQLAlchemy).
- `schemas.py`: Request/Response validation (Pydantic).
- `service.py`: Business logic and database operations.
- `views.py`: API endpoints.
- `urls.py`: App-specific router configuration.
- `admin.py`: Admin panel registration.

---

## 🗄️ 2. Define the Model (`models.py`)

Define your table structure using the `Base` class.

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

---

## 📝 3. Define Schemas (`schemas.py`)

Create Pydantic models for validation. **Always wrap responses in `BaseResponse`** for consistency.

```python
from pydantic import BaseModel
from project.core.responses import BaseResponse

class PostBase(BaseModel):
    title: str
    content: str

class PostCreate(PostBase):
    pass

class PostRead(PostBase):
    id: int

# Consistent Response Wrappers
class PostResponse(BaseResponse[PostRead]):
    pass

class PostListResponse(BaseResponse[list[PostRead]]):
    pass
```

---

## 🧠 4. Add Logic to Service (`service.py`)

All database interactions should live here. Use the `.objects` manager for a Django-like feel.

```python
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Post
from .schemas import PostCreate

async def get_posts(session: AsyncSession):
    return await Post.objects.all(session)

async def create_post(session: AsyncSession, data: PostCreate):
    return await Post.create(session, **data.model_dump())

async def delete_post(session: AsyncSession, post_id: int):
    post = await Post.objects.get(session, id=post_id)
    if post:
        await post.delete(session)
    return post
```

---

## 🌐 5. Implement Views (`views.py`)

Use the app's `router` to define endpoints. Autodiscovery will pick these up automatically.

```python
from fastapi import Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from project.core.db import get_async_session
from .urls import router
from . import service, schemas

@router.get("/", response_model=schemas.PostListResponse)
async def list_posts(session: AsyncSession = Depends(get_async_session)):
    posts = await service.get_posts(session)
    return schemas.PostListResponse(
        success=True,
        status_code=200,
        message="Posts retrieved",
        data=posts
    )

@router.post("/", response_model=schemas.PostResponse, status_code=201)
async def create_post(data: schemas.PostCreate, session: AsyncSession = Depends(get_async_session)):
    post = await service.create_post(session, data)
    return schemas.PostResponse(
        success=True,
        status_code=201,
        message="Post created",
        data=post
    )
```

---

## 🚀 Key Benefits of this flow:
1.  **Auto-Discovery**: Routers are registered the moment you add the app to `INSTALLED_APPS`.
2.  **Standard Responses**: Every API returns the same JSON envelope (`success`, `status_code`, `message`, `data`).
3.  **Clean Code**: Separating DB logic (Service) from HTTP logic (Views) keeps the project maintainable.
4.  **Django Similarity**: If you know Django, the folder structure and command-line habits stay the same.

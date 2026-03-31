# app/schemas/theory_post.py
# Pydantic Schemas für Theorie-Posts

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class TheoryPostCreate(BaseModel):
    """Schema zum Erstellen eines Theorie-Posts."""
    topic: str = Field(..., min_length=2, max_length=200, description="Theorie-Thema")
    content: str = Field(..., min_length=5, max_length=5000, description="Fachlicher Inhalt")
    source: Optional[str] = Field(None, max_length=300, description="Quellenangabe")


class TheoryPostUpdate(BaseModel):
    """Schema zum Bearbeiten — nur gesetzte Felder werden geändert."""
    topic: Optional[str] = Field(None, max_length=200)
    content: Optional[str] = Field(None, max_length=5000)
    source: Optional[str] = Field(None, max_length=300)
    caption: Optional[str] = None
    story_text: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(draft|ready|published)$")


class TheoryPostResponse(BaseModel):
    """Response-Schema für einen Theorie-Post."""
    id: int
    topic: str
    content: str
    source: Optional[str] = None
    caption: Optional[str] = None
    story_text: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TheoryPostListResponse(BaseModel):
    """Liste von Theorie-Posts."""
    total: int
    posts: list[TheoryPostResponse]


class TheoryGenerateResponse(BaseModel):
    """Generierter Content für einen Theorie-Post."""
    instagram_caption: str
    tiktok_description: str
    provider: str
    used_training_data: bool
    training_examples_count: int

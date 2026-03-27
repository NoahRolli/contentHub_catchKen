# app/schemas/scheduled_post.py
# ============================================================
# Pydantic Schemas für geplante Posts (Kalender).
# Validieren Eingaben beim Erstellen, Bearbeiten und Verschieben.
# ============================================================

from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional
from enum import Enum


class ContentTypeEnum(str, Enum):
    """Content-Typen für Farbcodierung im Kalender."""
    SUCCESS = "success"
    NEWS = "news"
    THEORY = "theory"
    REVIEW = "review"


class PlatformEnum(str, Enum):
    """Zielplattform für den Post."""
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    BOTH = "both"


class StatusEnum(str, Enum):
    """Status-Workflow: draft → ready → published."""
    DRAFT = "draft"
    READY = "ready"
    PUBLISHED = "published"


class ScheduledPostCreate(BaseModel):
    """Schema zum Erstellen eines neuen Kalender-Eintrags."""
    content_type: ContentTypeEnum
    scheduled_date: date
    scheduled_time: Optional[str] = Field(None, max_length=5, description="Uhrzeit z.B. '18:00'")
    platform: PlatformEnum = PlatformEnum.BOTH
    caption: Optional[str] = None
    hashtags: Optional[str] = None
    story_text: Optional[str] = None
    notes: Optional[str] = None


class ScheduledPostUpdate(BaseModel):
    """Schema zum Bearbeiten — nur gesetzte Felder werden geändert."""
    content_type: Optional[ContentTypeEnum] = None
    scheduled_date: Optional[date] = None
    scheduled_time: Optional[str] = Field(None, max_length=5)
    platform: Optional[PlatformEnum] = None
    caption: Optional[str] = None
    hashtags: Optional[str] = None
    story_text: Optional[str] = None
    status: Optional[StatusEnum] = None
    notes: Optional[str] = None


class ScheduledPostMove(BaseModel):
    """Schema für Drag & Drop — nur das Datum ändert sich."""
    scheduled_date: date


class ScheduledPostResponse(BaseModel):
    """Response-Schema für einen Kalender-Eintrag."""
    id: int
    user_id: int
    content_type: str
    scheduled_date: date
    scheduled_time: Optional[str] = None
    platform: str
    caption: Optional[str] = None
    hashtags: Optional[str] = None
    story_text: Optional[str] = None
    status: str
    notes: Optional[str] = None
    published_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
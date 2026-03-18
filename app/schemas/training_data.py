# app/schemas/training_data.py
# ============================================================
# Pydantic Schemas für Trainingsdaten.
# Validieren die Eingabe beim Upload (CSV, manuell, Instagram JSON)
# und formatieren die API-Responses.
# ============================================================

from pydantic import BaseModel, Field  # BaseModel = Pydantic Basis, Field = Validierungsregeln
from datetime import datetime
from enum import Enum


# --- Enums (müssen zu den SQLAlchemy Enums im Model passen!) ---

class PlatformSchema(str, Enum):
    """Plattform-Auswahl für API-Requests."""
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"


class ContentTypeSchema(str, Enum):
    """Content-Typ für API-Requests."""
    SUCCESS = "success"
    NEWS = "news"
    THEORY = "theory"
    REVIEW = "review"


# --- Schema für einzelnen manuellen Upload ---

class TrainingPostCreate(BaseModel):
    """
    Schema wenn jemand EINEN Trainings-Post manuell eingibt.
    z.B. über ein Formular im Frontend oder direkt via API.
    """
    platform: PlatformSchema  # "instagram" oder "tiktok"
    content_type: ContentTypeSchema  # "success", "news", etc.
    caption: str = Field(
        ...,              # ... = Pflichtfeld (required)
        min_length=5,     # Mindestens 5 Zeichen — ein Post mit weniger ist sinnlos
        max_length=5000,  # Instagram-Limit ist 2200, aber wir lassen etwas Spielraum
        description="Die Caption / Beschreibung des Posts"
    )
    hashtags: str | None = Field(
        default=None,
        max_length=2000,
        description="Hashtags des Posts (optional, z.B. '#fahrschule #bestanden')"
    )
    source_url: str | None = Field(
        default=None,
        max_length=500,
        description="Original-URL des Posts (optional, für Duplikat-Erkennung)"
    )
    original_date: datetime | None = Field(
        default=None,
        description="Veröffentlichungsdatum des Original-Posts (optional)"
    )


# --- Schema für Bulk-Upload via CSV ---

class TrainingPostBulkItem(BaseModel):
    """
    Ein einzelner Eintrag innerhalb eines CSV/Bulk-Uploads.
    Einfacher als TrainingPostCreate — platform und content_type
    werden für den ganzen Batch gesetzt, nicht pro Zeile.
    """
    caption: str = Field(..., min_length=5, max_length=5000)
    hashtags: str | None = None
    source_url: str | None = None
    original_date: datetime | None = None


class TrainingPostBulkUpload(BaseModel):
    """
    Schema für Bulk-Upload: Mehrere Posts auf einmal hochladen.
    Platform und Content-Type gelten für ALLE Posts im Batch.
    """
    platform: PlatformSchema
    content_type: ContentTypeSchema
    posts: list[TrainingPostBulkItem] = Field(
        ...,
        min_length=1,       # Mindestens 1 Post
        max_length=500,      # Max 500 Posts pro Upload (Sicherheitslimit)
        description="Liste der Trainings-Posts zum Importieren"
    )


# --- Response Schema (was die API zurückgibt) ---

class TrainingPostResponse(BaseModel):
    """
    Response-Schema für einen einzelnen Trainings-Post.
    model_config erlaubt das direkte Befüllen aus SQLAlchemy-Objekten.
    """
    id: int
    platform: PlatformSchema
    content_type: ContentTypeSchema
    caption: str
    hashtags: str | None
    source_url: str | None
    original_date: datetime | None
    created_at: datetime

    model_config = {
        "from_attributes": True  # Erlaubt: TrainingPostResponse.model_validate(db_objekt)
    }


# --- Statistik-Response ---

class TrainingDataStats(BaseModel):
    """
    Übersicht über die vorhandenen Trainingsdaten.
    Wird im Frontend angezeigt: "12 Instagram-Posts, 3 TikTok-Posts geladen"
    """
    total_count: int                         # Gesamtanzahl aller Trainings-Posts
    by_platform: dict[str, int]              # z.B. {"instagram": 12, "tiktok": 3}
    by_content_type: dict[str, int]          # z.B. {"success": 10, "news": 5}
    has_training_data: bool                  # True wenn mindestens 1 Post vorhanden
    oldest_post: datetime | None             # Ältester Trainings-Post
    newest_post: datetime | None             # Neuester Trainings-Post
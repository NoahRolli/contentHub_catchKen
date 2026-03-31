# student_success.py – Pydantic Schemas für Erfolgs-Posts
# Definiert wie Daten bei der API rein (Request) und raus (Response) gehen
# Pydantic validiert automatisch alle Eingaben
from pydantic import BaseModel, Field  # Basisklasse für Schemas
from datetime import date, datetime  # Datum und Zeitstempel
from typing import Optional  # Für optionale Felder
class StudentSuccessCreate(BaseModel):
    """Schema für das ERSTELLEN eines Erfolgs-Posts."""

    student_name: Optional[str] = Field(None, max_length=100)
    exam_date: date = Field(..., description="Datum der bestandenen Prüfung")
    category: str = Field("B", max_length=10)
    consent_given: bool = Field(..., description="Einverständnis Bildnutzung (Pflicht)")
    details: Optional[str] = Field(None, max_length=500, description="Zusatzinfos für LLM")
class StudentSuccessUpdate(BaseModel):
    """Schema für das BEARBEITEN — nur gesetzte Felder werden geändert."""

    student_name: Optional[str] = Field(None, max_length=100)
    exam_date: Optional[date] = None
    category: Optional[str] = Field(None, max_length=10)
    details: Optional[str] = Field(None, max_length=500)
    caption: Optional[str] = None
    story_text: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(draft|ready|published)$")
class StudentSuccessResponse(BaseModel):
    """Schema für die API-ANTWORT – was der Client zurückbekommt.
    
    Enthält alle Felder inklusive der generierten und automatischen Werte.
    """
    
    id: int
    user_id: int
    student_name: Optional[str] = None
    exam_date: date
    category: str
    image_path: Optional[str] = None
    image_paths: Optional[list] = None
    consent_given: bool
    details: Optional[str] = None
    caption: Optional[str] = None
    story_text: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True  # Erlaubt Konvertierung von SQLAlchemy-Objekten zu Pydantic
class StudentSuccessListResponse(BaseModel):
    """Schema für eine LISTE von Erfolgs-Posts.
    
    Enthält die Posts plus Metadaten (Gesamtanzahl, Pagination).
    """
    
    total: int  # Gesamtanzahl aller Posts
    posts: list[StudentSuccessResponse]  # Die eigentlichen Posts


# ============================================================
# Phase 3: LLM Content-Generierung
# ============================================================

class GenerateContentRequest(BaseModel):
    """Schema für den Generate-Request.
    
    Optionale Felder um die Generierung zu steuern.
    student_name und exam_type werden vom Post geholt,
    aber details kann man extra mitgeben.
    """
    details: Optional[str] = Field(
        None,
        description="Zusätzliche Details für die Generierung (z.B. 'beim ersten Versuch bestanden')",
        max_length=500
    )
    use_training_data: bool = Field(
        True,  # Default: Trainingsdaten nutzen wenn vorhanden
        description="Soll der LLM Beispiel-Posts als Vorlage nutzen?"
    )


class GenerateContentResponse(BaseModel):
    """Schema für den generierten Content (Instagram + TikTok).

    Caption und Hashtags sind in einem Text zusammengefasst —
    kein separates Hashtag-Feld mehr.
    """
    instagram_caption: str = Field(description="Fertiger Instagram Post-Text inkl. Hashtags")
    tiktok_description: str = Field(description="Fertige TikTok-Beschreibung inkl. Hashtags")
    provider: str = Field(description="Welcher LLM Provider wurde genutzt (ollama/openai)")
    used_training_data: bool = Field(description="Wurden Trainingsdaten für Few-Shot genutzt?")
    training_examples_count: int = Field(description="Anzahl verwendeter Trainingsbeispiele")
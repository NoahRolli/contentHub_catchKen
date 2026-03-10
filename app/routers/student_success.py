# student_success.py – Pydantic Schemas für Erfolgs-Posts
# Definiert wie Daten bei der API rein (Request) und raus (Response) gehen
# Pydantic validiert automatisch alle Eingaben

from pydantic import BaseModel, Field  # Basisklasse für Schemas
from datetime import date, datetime  # Datum und Zeitstempel
from typing import Optional  # Für optionale Felder


class StudentSuccessCreate(BaseModel):
    """Schema für das ERSTELLEN eines Erfolgs-Posts.
    
    Das sind die Felder die der Admin im Formular ausfüllt.
    Das Bild wird separat hochgeladen (nicht als JSON).
    """
    
    student_name: Optional[str] = Field(
        None,  # Optional – nicht jeder will seinen Namen
        description="Vorname des Schülers (optional)",
        max_length=100
    )
    exam_date: date = Field(
        ...,  # ... = Pflichtfeld
        description="Datum der bestandenen Prüfung"
    )
    category: str = Field(
        "B",  # Standardwert
        description="Führerschein-Kategorie (z.B. B, A, A1)",
        max_length=10
    )
    consent_given: bool = Field(
        ...,  # Pflichtfeld – muss True sein
        description="Einverständnis für Bildnutzung (PFLICHT)"
    )


class StudentSuccessUpdate(BaseModel):
    """Schema für das BEARBEITEN eines Erfolgs-Posts.
    
    Alle Felder sind optional – nur das was sich ändert wird mitgeschickt.
    """
    
    student_name: Optional[str] = Field(None, max_length=100)
    exam_date: Optional[date] = None
    category: Optional[str] = Field(None, max_length=10)
    caption: Optional[str] = None  # Generierte Caption bearbeiten
    hashtags: Optional[str] = None  # Generierte Hashtags bearbeiten
    story_text: Optional[str] = None  # Story-Text bearbeiten
    status: Optional[str] = Field(None, pattern="^(draft|ready|published)$")  # Nur gültige Status


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
    consent_given: bool
    caption: Optional[str] = None
    hashtags: Optional[str] = None
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
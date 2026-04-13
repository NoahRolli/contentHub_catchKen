# app/schemas/news.py
# Pydantic Schemas für RSS-News und Content-Quellen

from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional


# === Content-Quellen (RSS-Feeds) ===

class ContentSourceCreate(BaseModel):
    """Schema zum Hinzufügen einer RSS-Quelle."""
    name: str = Field(..., min_length=2, max_length=200, description="Name der Quelle")
    url: str = Field(..., description="RSS-Feed URL")
    keywords: Optional[str] = Field(None, description="Kommagetrennte Keywords zum Filtern")
    scan_interval: int = Field(60, ge=5, le=1440, description="Scan-Intervall in Minuten")


class ContentSourceResponse(BaseModel):
    """Response für eine Quelle."""
    id: int
    name: str
    source_type: str
    url: str
    is_active: bool
    scan_interval: int
    last_scanned_at: Optional[datetime] = None
    keywords: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# === News-Items (gescannte Artikel) ===

class NewsItemResponse(BaseModel):
    """Response für einen gescannten Artikel."""
    id: int
    source_id: int
    title: str
    url: str
    summary: Optional[str] = None
    published_at: Optional[datetime] = None
    keywords_matched: Optional[str] = None
    is_relevant: bool
    is_processed: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# === Scan-Ergebnis ===

class ScanResult(BaseModel):
    """Ergebnis eines Feed-Scans."""
    scanned: int = Field(description="Anzahl gescannter Quellen")
    new_items: int = Field(description="Anzahl neuer Artikel")


# === News-Post Generierung ===

class NewsGenerateResponse(BaseModel):
    """Generierter Content für einen News-Artikel."""
    instagram_caption: str
    tiktok_description: str
    provider: str
    used_training_data: bool
    training_examples_count: int

# content_source.py – Datenbank-Modell für Content-Quellen
# Speichert die verschiedenen Quellen aus denen Content generiert wird
# Beispiele: RSS-Feeds (SRF, 20min), Google Reviews, etc.

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text  # Spaltentypen
from sqlalchemy.sql import func  # Für automatische Zeitstempel
from app.core.database import Base  # Basisklasse für alle Modelle


class ContentSource(Base):
    """Content-Quellen – woher das System automatisch Inhalte bezieht.
    
    Typen:
        - "rss": RSS-Feed einer Newsseite (z.B. SRF, 20min, Blick)
        - "google_reviews": Google Reviews der Fahrschule
    
    Workflow:
        1. Admin fügt eine Quelle hinzu (z.B. SRF RSS-URL)
        2. System scannt die Quelle regelmässig (Background Job)
        3. Gefundene Inhalte landen in NewsItem oder als Review
    
    Felder:
        id:              Eindeutige ID
        name:            Anzeigename (z.B. "SRF News")
        source_type:     Art der Quelle (rss / google_reviews)
        url:             URL der Quelle (RSS-Feed-URL oder Google Place ID)
        is_active:       Ist die Quelle aktiv? (kann pausiert werden)
        scan_interval:   Wie oft scannen in Minuten (z.B. 60 = jede Stunde)
        last_scanned_at: Wann wurde zuletzt gescannt
        keywords:        Kommagetrennte Keywords zum Filtern (z.B. "Unfall,Verkehr,Auto")
        description:     Optionale Beschreibung der Quelle
        created_at:      Erstelldatum
        updated_at:      Letztes Update
    """
    
    # Name der Tabelle in der Datenbank
    __tablename__ = "content_sources"
    
    # === Primärschlüssel ===
    id = Column(Integer, primary_key=True, index=True)  # Auto-increment ID
    
    # === Quellen-Daten ===
    name = Column(String, nullable=False)  # Anzeigename (z.B. "SRF News")
    source_type = Column(String, nullable=False)  # "rss" oder "google_reviews"
    url = Column(String, nullable=False)  # Feed-URL oder Google Place ID
    
    # === Steuerung ===
    is_active = Column(Boolean, default=True)  # Quelle aktiv oder pausiert
    scan_interval = Column(Integer, default=60)  # Scan-Intervall in Minuten
    last_scanned_at = Column(DateTime(timezone=True), nullable=True)  # Letzter Scan-Zeitpunkt
    
    # === Filterung ===
    keywords = Column(String, nullable=True)  # Kommagetrennte Keywords: "Unfall,Verkehr,Auto"
    
    # === Zusatzinfo ===
    description = Column(Text, nullable=True)  # Optionale Beschreibung
    
    # === Zeitstempel ===
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Erstelldatum
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())  # Letztes Update
    
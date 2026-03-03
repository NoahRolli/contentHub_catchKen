# news_item.py – Datenbank-Modell für gescannte Nachrichtenartikel
# Speichert einzelne Artikel die aus RSS-Feeds extrahiert wurden
# Jeder Artikel wird analysiert und kann zu einem News-Post werden

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey  # Spaltentypen
from sqlalchemy.sql import func  # Für automatische Zeitstempel
from sqlalchemy.orm import relationship  # Für Beziehungen zwischen Tabellen
from app.core.database import Base  # Basisklasse für alle Modelle


class NewsItem(Base):
    """Nachrichtenartikel – aus RSS-Feeds extrahierte Artikel.
    
    Workflow:
        1. RSS-Scanner findet neuen Artikel
        2. Keyword-Filter prüft Relevanz (Unfall, Verkehr, etc.)
        3. Artikel wird gespeichert und durch LLM analysiert
        4. LLM entscheidet: geeignet für Sicherheits-Post oder allgemeine Prävention
        5. Bei Eignung wird ein ContentIdea/ScheduledPost daraus generiert
    
    Felder:
        id:               Eindeutige ID
        source_id:        Von welcher ContentSource stammt der Artikel (FK)
        title:            Artikel-Titel aus dem RSS-Feed
        url:              Original-URL zum Artikel
        summary:          Kurze Zusammenfassung (aus Feed oder LLM)
        content_extract:  Extrahierter Artikeltext (NICHT vollständig – nur Zusammenfassung)
        published_at:     Wann wurde der Artikel veröffentlicht
        keywords_matched: Welche Keywords haben gematcht (z.B. "Unfall,Verkehr")
        is_relevant:      Hat der LLM den Artikel als relevant eingestuft?
        is_processed:     Wurde der Artikel bereits verarbeitet?
        prevention_type:  Art des Posts: "specific" (konkreter Unfall) oder "general" (allgemein)
        created_at:       Wann wurde der Artikel gespeichert
    """
    
    # Name der Tabelle in der Datenbank
    __tablename__ = "news_items"
    
    # === Primärschlüssel ===
    id = Column(Integer, primary_key=True, index=True)  # Auto-increment ID
    
    # === Beziehung zur Content-Quelle ===
    source_id = Column(Integer, ForeignKey("content_sources.id"), nullable=False)  # Aus welchem Feed?
    source = relationship("ContentSource", backref="news_items")  # Ermöglicht source.news_items
    
    # === Artikel-Daten ===
    title = Column(String, nullable=False)  # Titel des Artikels
    url = Column(String, nullable=False, unique=True)  # Original-URL (unique verhindert Duplikate)
    summary = Column(Text, nullable=True)  # Kurze Zusammenfassung
    content_extract = Column(Text, nullable=True)  # Extrahierter Text (nur Zusammenfassung, kein Volltext!)
    published_at = Column(DateTime(timezone=True), nullable=True)  # Veröffentlichungsdatum des Artikels
    
    # === Analyse-Ergebnisse ===
    keywords_matched = Column(String, nullable=True)  # Welche Keywords gematcht haben
    is_relevant = Column(Boolean, default=False)  # LLM-Bewertung: relevant für Post?
    is_processed = Column(Boolean, default=False)  # Wurde schon ein Post daraus generiert?
    prevention_type = Column(String, nullable=True)  # "specific" oder "general"
    
    # === Zeitstempel ===
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Wann gespeichert
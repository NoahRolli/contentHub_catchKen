# content_idea.py – Datenbank-Modell für generierte Content-Vorschläge
# Speichert LLM-generierte Ideen die noch nicht eingeplant sind
# Dient als "Ideenpool" in der Sidebar des Kalenders

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey  # Spaltentypen
from sqlalchemy.sql import func  # Für automatische Zeitstempel
from sqlalchemy.orm import relationship  # Für Beziehungen zwischen Tabellen
from app.core.database import Base  # Basisklasse für alle Modelle


class ContentIdea(Base):
    """Content-Vorschläge – LLM-generierte Ideen im Wartepool.
    
    Das ist die "Zwischenstation" zwischen Rohdaten und geplantem Post.
    Ideen erscheinen in der Sidebar und können per Drag & Drop
    in den Kalender gezogen werden.
    
    Typen:
        - "success": Vorschlag basierend auf einem Erfolgs-Post
        - "news": Vorschlag basierend auf einem Nachrichtenartikel
        - "theory": Vorschlag für einen Theorie-Post
        - "review": Vorschlag basierend auf einer Google Review
    
    Workflow:
        1. System generiert Idee (aus News, Theorie, Review oder Erfolg)
        2. Idee erscheint in der Sidebar als Vorschlag
        3. Admin zieht Idee in den Kalender → wird zu ScheduledPost
        4. Oder: Admin verwirft die Idee
    
    Felder:
        id:              Eindeutige ID
        content_type:    Art des Contents (success/news/theory/review)
        title:           Kurzer Titel für die Sidebar-Anzeige
        caption:         Generierte Caption (bearbeitbar)
        hashtags:        Generierte Hashtags
        story_text:      Optionaler Story-Text
        quiz_data:       Quiz-Fragen als JSON (nur bei Theorie-Posts)
        carousel_text:   Carousel-Slides als Text (nur bei Theorie-Posts)
        tiktok_script:   TikTok-Skript (nur bei Theorie-Posts)
        source_ref_id:   ID der Ursprungsquelle (NewsItem, Review, etc.)
        source_ref_type: Typ der Ursprungsquelle (zur Zuordnung)
        is_used:         Wurde die Idee bereits eingeplant?
        is_dismissed:    Wurde die Idee verworfen?
        created_at:      Erstelldatum
    """
    
    # Name der Tabelle in der Datenbank
    __tablename__ = "content_ideas"
    
    # === Primärschlüssel ===
    id = Column(Integer, primary_key=True, index=True)  # Auto-increment ID
    
    # === Content-Typ ===
    content_type = Column(String, nullable=False)  # success / news / theory / review
    
    # === Generierter Content ===
    title = Column(String, nullable=False)  # Kurztitel für Sidebar
    caption = Column(Text, nullable=True)  # LLM-generierte Caption
    hashtags = Column(String, nullable=True)  # LLM-generierte Hashtags
    story_text = Column(Text, nullable=True)  # Optionaler Story-Text
    
    # === Theorie-spezifische Felder ===
    quiz_data = Column(Text, nullable=True)  # JSON: [{frage, antworten, korrekt}, ...]
    carousel_text = Column(Text, nullable=True)  # Text für 3-Slide Carousel
    tiktok_script = Column(Text, nullable=True)  # 25-30 Sek TikTok-Skript
    
    # === Referenz zur Ursprungsquelle ===
    source_ref_id = Column(Integer, nullable=True)  # ID des Ursprungs (NewsItem, etc.)
    source_ref_type = Column(String, nullable=True)  # "news_item", "review", "theory_topic"
    
    # === Status ===
    is_used = Column(String, default=False)  # Bereits zu ScheduledPost geworden?
    is_dismissed = Column(String, default=False)  # Vom Admin verworfen?
    
    # === Zeitstempel ===
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Erstelldatum
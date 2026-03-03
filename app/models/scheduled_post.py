# scheduled_post.py – Datenbank-Modell für geplante Posts
# Das zentrale Modell des Kalenders – jeder Post der eingeplant wird landet hier
# Verbindet Content-Ideen mit einem Datum und Status

from sqlalchemy import Column, Integer, String, DateTime, Date, Text, ForeignKey  # Spaltentypen
from sqlalchemy.sql import func  # Für automatische Zeitstempel
from sqlalchemy.orm import relationship  # Für Beziehungen zwischen Tabellen
from app.core.database import Base  # Basisklasse für alle Modelle


class ScheduledPost(Base):
    """Geplante Posts – das Herzstück des Kalenders.
    
    Jeder Eintrag im Kalender ist ein ScheduledPost.
    Er referenziert genau einen Content-Typ und hat ein geplantes Datum.
    
    Workflow:
        1. Admin zieht ContentIdea aus Sidebar in den Kalender
        2. ScheduledPost wird erstellt mit Status "draft"
        3. Admin bearbeitet Caption, Hashtags, Datum
        4. Admin gibt frei → Status "ready"
        5. Nach Export/Posting → Status "published"
    
    Farbcodierung im Kalender:
        - 🟢 Grün = success (Erfolgs-Post)
        - 🔴 Rot = news (News-Post)
        - 🔵 Blau = theory (Theorie-Post)
        - 🟡 Gelb = review (Rezension)
    
    Felder:
        id:              Eindeutige ID
        user_id:         Welcher Admin hat den Post eingeplant (FK → users)
        content_idea_id: Aus welcher Idee stammt der Post (FK → content_ideas)
        content_type:    Art des Contents (success/news/theory/review)
        scheduled_date:  Geplantes Veröffentlichungsdatum
        scheduled_time:  Geplante Uhrzeit (optional)
        platform:        Zielplattform (instagram/tiktok/both)
        caption:         Finale Caption (kopiert aus Idee, bearbeitbar)
        hashtags:        Finale Hashtags (kopiert aus Idee, bearbeitbar)
        story_text:      Optionaler Story-Text
        status:          Aktueller Status (draft/ready/published)
        published_at:    Wann wurde tatsächlich gepostet/exportiert
        notes:           Interne Notizen vom Admin
        created_at:      Erstelldatum
        updated_at:      Letztes Update
    """
    
    # Name der Tabelle in der Datenbank
    __tablename__ = "scheduled_posts"
    
    # === Primärschlüssel ===
    id = Column(Integer, primary_key=True, index=True)  # Auto-increment ID
    
    # === Beziehungen ===
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Wer hat eingeplant?
    user = relationship("User", backref="scheduled_posts")  # Ermöglicht user.scheduled_posts
    
    content_idea_id = Column(Integer, ForeignKey("content_ideas.id"), nullable=True)  # Aus welcher Idee?
    content_idea = relationship("ContentIdea", backref="scheduled_posts")  # Ermöglicht idea.scheduled_posts
    
    # === Content-Typ (für Farbcodierung im Kalender) ===
    content_type = Column(String, nullable=False)  # success / news / theory / review
    
    # === Planung ===
    scheduled_date = Column(Date, nullable=False)  # Wann soll gepostet werden?
    scheduled_time = Column(String, nullable=True)  # Optionale Uhrzeit (z.B. "18:00")
    platform = Column(String, default="both")  # instagram / tiktok / both
    
    # === Finaler Content (bearbeitbar) ===
    caption = Column(Text, nullable=True)  # Finale Caption
    hashtags = Column(String, nullable=True)  # Finale Hashtags
    story_text = Column(Text, nullable=True)  # Optionaler Story-Text
    
    # === Status ===
    status = Column(String, default="draft")  # draft → ready → published
    published_at = Column(DateTime(timezone=True), nullable=True)  # Tatsächliches Posting-Datum
    
    # === Zusatzinfo ===
    notes = Column(Text, nullable=True)  # Interne Notizen vom Admin
    
    # === Zeitstempel ===
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Erstelldatum
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())  # Letztes Update
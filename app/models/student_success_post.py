# student_success_post.py – Datenbank-Modell für Erfolgs-Posts
# Speichert bestandene Fahrprüfungen als Social-Media-Content
# Jeder Post enthält Schülerdaten, Bild und generierten Content

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey, Text  # Spaltentypen
from sqlalchemy.sql import func  # Für automatische Zeitstempel
from sqlalchemy.orm import relationship  # Für Beziehungen zwischen Tabellen
from app.core.database import Base  # Basisklasse für alle Modelle


class StudentSuccessPost(Base):
    """Erfolgs-Posts – bestandene Fahrschüler:innen als Social-Media-Content.
    
    Workflow:
        1. Admin lädt Bild hoch + gibt Daten ein
        2. LLM generiert Caption + Hashtags
        3. Post landet als DRAFT im Kalender
        4. Admin prüft und gibt frei
    
    Felder:
        id:              Eindeutige ID
        user_id:         Welcher Admin hat den Post erstellt (FK → users)
        student_name:    Vorname des Schülers (optional, für Caption)
        exam_date:       Prüfungsdatum
        category:        Führerschein-Kategorie (z.B. B, A, A1)
        image_path:      Pfad zum Bild auf der SSD (media/uploads/...)
        consent_given:   Einverständnis für Bildnutzung (PFLICHTFELD)
        caption:         Generierte oder bearbeitete Caption
        hashtags:        Generierte oder bearbeitete Hashtags
        story_text:      Optionaler Text für Instagram Story
        status:          Aktueller Status (draft/ready/published)
        created_at:      Erstelldatum
        updated_at:      Letztes Update
    """
    
    # Name der Tabelle in der Datenbank
    __tablename__ = "student_success_posts"
    
    # === Primärschlüssel ===
    id = Column(Integer, primary_key=True, index=True)  # Auto-increment ID
    
    # === Beziehung zum Admin der den Post erstellt hat ===
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Wer hat den Post erstellt?
    user = relationship("User", backref="success_posts")  # Ermöglicht user.success_posts
    
    # === Schüler-Daten ===
    student_name = Column(String, nullable=True)  # Optional – nicht jeder will seinen Namen
    exam_date = Column(Date, nullable=False)  # Wann wurde die Prüfung bestanden
    category = Column(String, nullable=False, default="B")  # Führerschein-Kategorie (B, A, A1 etc.)
    
    # === Bild & Consent ===
    image_path = Column(String, nullable=True)  # Pfad zum Bild (media/uploads/success/...)
    consent_given = Column(Boolean, nullable=False)  # PFLICHT: Einverständnis für Bildnutzung
    
    # === Generierter Content ===
    caption = Column(Text, nullable=True)  # LLM-generierte Caption (bearbeitbar)
    hashtags = Column(String, nullable=True)  # LLM-generierte Hashtags (bearbeitbar)
    story_text = Column(Text, nullable=True)  # Optionaler Instagram Story Text
    
    # === Status im Planungssystem ===
    status = Column(String, default="draft")  # draft → ready → published
    
    # === Zeitstempel ===
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Erstelldatum
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())  # Letztes Update
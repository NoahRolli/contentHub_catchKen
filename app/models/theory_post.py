# app/models/theory_post.py
# ============================================================
# Datenbank-Modell für Theorie-Posts.
# Fahrschultheorie (Vortritt, Signale, etc.) als Social-Media-Content.
# Der Admin gibt den Theorie-Inhalt ein, der LLM formuliert ihn
# für Instagram/TikTok um.
# ============================================================

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
from app.core.database import Base


class TheoryPost(Base):
    """Theorie-Posts — Fahrschultheorie als Social-Media-Content.

    Workflow:
        1. Admin gibt Theorie-Thema + Inhalt ein (z.B. "Vortrittsregel rechts")
        2. LLM formuliert den Inhalt als Instagram/TikTok Post
        3. Admin prüft, passt an, plant ein
    """

    __tablename__ = "theory_posts"

    # Primärschlüssel
    id = Column(Integer, primary_key=True, index=True)

    # Thema (z.B. "Vortrittsregel", "Lichtsignale", "Autobahn-Auffahrt")
    topic = Column(String, nullable=False)

    # Theorie-Inhalt: der fachliche Text den Ken liefert
    content = Column(Text, nullable=False)

    # Quelle: woher stammt der Inhalt (z.B. "Theoriebuch S. 42", "ASA Fragenkatalog")
    source = Column(String, nullable=True)

    # Generierter Content
    caption = Column(Text, nullable=True)       # Instagram Post-Text
    story_text = Column(Text, nullable=True)    # TikTok Beschreibung

    # Status
    status = Column(String, default="draft")    # draft → ready → published

    # Zeitstempel
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

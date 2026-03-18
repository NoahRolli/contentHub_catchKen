# app/models/training_post.py
# ============================================================
# Datenbank-Model für Trainingsdaten (echte Instagram-Posts).
# Diese Posts werden als Few-Shot Examples an den LLM gefüttert,
# damit er den Style deines Kollegen imitieren kann.
# Ohne Trainingsdaten → generischer Prompt.
# Mit Trainingsdaten → LLM schreibt im gleichen Style.
# ============================================================

from sqlalchemy import Column, Integer, String, Text, DateTime, Enum  # Spaltentypen
from sqlalchemy import func  # func.now() für automatische Timestamps
import enum  # Python's Enum für Plattform-Auswahl

from app.core.database import Base  # Unsere SQLAlchemy Base-Klasse


class Platform(str, enum.Enum):
    """
    Für welche Plattform ist dieser Trainings-Post?
    str + enum.Enum = Werte werden als Strings in der DB gespeichert,
    nicht als Integers — besser lesbar bei direktem DB-Zugriff.
    """
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"


class ContentType(str, enum.Enum):
    """
    Welcher Content-Typ ist der Trainings-Post?
    Aktuell nur SUCCESS (Erfolgs-Posts), aber vorbereitet für
    spätere Phasen: NEWS, THEORY, REVIEW.
    """
    SUCCESS = "success"      # Phase 3: Erfolgs-Posts ("bestanden!")
    NEWS = "news"            # Phase 5: News-Posts (RSS)
    THEORY = "theory"        # Phase 4: Theorie-Posts
    REVIEW = "review"        # Phase 6: Google Reviews


class TrainingPost(Base):
    """
    Ein einzelner Trainings-Post aus dem echten Instagram/TikTok-Account.
    Wird beim Import (CSV oder Instagram JSON) in die DB geschrieben
    und beim Generieren als Few-Shot Example dem LLM mitgegeben.
    """

    __tablename__ = "training_posts"  # Tabellenname in SQLite/PostgreSQL

    # --- Primärschlüssel ---
    id = Column(
        Integer,
        primary_key=True,
        index=True  # Index für schnellere Abfragen
    )

    # --- Plattform (Instagram oder TikTok) ---
    # Wichtig für die Trennung: Instagram-Style ≠ TikTok-Style
    platform = Column(
        Enum(Platform),
        nullable=False,  # Muss immer gesetzt sein
        index=True       # Oft gefiltert → Index für Performance
    )

    # --- Content-Typ (Success, News, Theory, Review) ---
    # Damit der LLM nur relevante Beispiele bekommt:
    # Erfolgs-Post generieren → nur SUCCESS-Trainingsbeispiele laden
    content_type = Column(
        Enum(ContentType),
        nullable=False,
        index=True
    )

    # --- Die eigentliche Caption / Beschreibung ---
    # Text = unbegrenzte Länge (im Gegensatz zu String(255))
    caption = Column(
        Text,
        nullable=False  # Ein Trainings-Post ohne Text ergibt keinen Sinn
    )

    # --- Hashtags (separat gespeichert) ---
    # Separat, damit der LLM Caption und Hashtags getrennt lernen kann.
    # Manche Posts haben evtl. keine Hashtags → nullable=True
    hashtags = Column(
        Text,
        nullable=True
    )

    # --- Originalquelle (z.B. Instagram Post-URL) ---
    # Optional, aber hilfreich um Duplikate zu erkennen beim Re-Import
    source_url = Column(
        String(500),
        nullable=True
    )

    # --- Veröffentlichungsdatum des Original-Posts ---
    # Damit wir z.B. nur neuere Posts als Beispiele nehmen können
    original_date = Column(
        DateTime,
        nullable=True  # Nicht immer aus dem Export verfügbar
    )

    # --- Automatische Timestamps ---
    created_at = Column(
        DateTime,
        server_default=func.now()  # Wird automatisch beim INSERT gesetzt
    )

    def __repr__(self):
        """Lesbare Darstellung für Debugging/Logging."""
        # Zeigt nur die ersten 50 Zeichen der Caption an
        preview = self.caption[:50] + "..." if len(self.caption) > 50 else self.caption
        return f"<TrainingPost id={self.id} platform={self.platform} type={self.content_type} '{preview}'>"
# asset.py – Datenbank-Modell für Medien-Dateien (Bilder, Videos)
# Speichert Informationen zu hochgeladenen Dateien
# Assets werden mit ScheduledPosts verknüpft (ein Post kann mehrere Assets haben)

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey  # Spaltentypen
from sqlalchemy.sql import func  # Für automatische Zeitstempel
from sqlalchemy.orm import relationship  # Für Beziehungen zwischen Tabellen
from app.core.database import Base  # Basisklasse für alle Modelle


class Asset(Base):
    """Medien-Dateien – Bilder und Videos die zu Posts gehören.
    
    Alle Dateien liegen physisch auf der SSD (media/uploads/...).
    In der Datenbank speichern wir nur den Pfad und Metadaten.
    
    Ein ScheduledPost kann mehrere Assets haben:
        - Hauptbild
        - Carousel-Slides
        - Video für TikTok
        - Story-Bild
    
    Felder:
        id:              Eindeutige ID
        scheduled_post_id: Zu welchem Post gehört das Asset (FK → scheduled_posts)
        file_path:       Pfad zur Datei auf der SSD (media/uploads/...)
        file_name:       Originaler Dateiname (z.B. "foto_max.jpg")
        file_type:       MIME-Type der Datei (z.B. "image/jpeg", "video/mp4")
        file_size:       Dateigrösse in Bytes
        asset_type:      Verwendungszweck (main_image/carousel/video/story)
        sort_order:      Reihenfolge bei Carousels (1, 2, 3...)
        created_at:      Wann wurde die Datei hochgeladen
    """
    
    # Name der Tabelle in der Datenbank
    __tablename__ = "assets"
    
    # === Primärschlüssel ===
    id = Column(Integer, primary_key=True, index=True)  # Auto-increment ID
    
    # === Beziehung zum Post ===
    scheduled_post_id = Column(Integer, ForeignKey("scheduled_posts.id"), nullable=True)  # Zu welchem Post?
    scheduled_post = relationship("ScheduledPost", backref="assets")  # Ermöglicht post.assets
    
    # === Datei-Informationen ===
    file_path = Column(String, nullable=False)  # Pfad auf SSD (media/uploads/success/foto.jpg)
    file_name = Column(String, nullable=False)  # Originaler Dateiname
    file_type = Column(String, nullable=False)  # MIME-Type (image/jpeg, video/mp4, etc.)
    file_size = Column(Integer, nullable=True)  # Dateigrösse in Bytes
    
    # === Verwendung ===
    asset_type = Column(String, default="main_image")  # main_image / carousel / video / story
    sort_order = Column(Integer, default=0)  # Reihenfolge bei Carousels (1, 2, 3...)
    
    # === Zeitstempel ===
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Upload-Datum
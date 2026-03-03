# user.py – Datenbank-Modell für Benutzer
# Definiert die "users" Tabelle in der Datenbank
# Jeder Benutzer kann Posts erstellen, planen und verwalten

from sqlalchemy import Column, Integer, String, Boolean, DateTime  # Spaltentypen
from sqlalchemy.sql import func  # Für automatische Zeitstempel
from app.core.database import Base  # Basisklasse für alle Modelle


class User(Base):
    """Benutzer-Tabelle – speichert Admin-Accounts für das Planungstool.
    
    Felder:
        id:              Eindeutige ID (wird automatisch vergeben)
        email:           E-Mail-Adresse (einzigartig, dient als Login)
        username:        Anzeigename im System
        hashed_password: Gehashtes Passwort (nie im Klartext!)
        is_active:       Ist der Account aktiv? (für späteres Deaktivieren)
        is_admin:        Hat Admin-Rechte? (für Rollen-System)
        created_at:      Wann wurde der Account erstellt
        updated_at:      Wann wurde der Account zuletzt geändert
    """
    
    # Name der Tabelle in der Datenbank
    __tablename__ = "users"
    
    # === Primärschlüssel ===
    id = Column(Integer, primary_key=True, index=True)  # Auto-increment ID
    
    # === Benutzer-Daten ===
    email = Column(String, unique=True, index=True, nullable=False)  # Eindeutige E-Mail
    username = Column(String, nullable=False)  # Anzeigename
    hashed_password = Column(String, nullable=False)  # Passwort-Hash (aus security.py)
    
    # === Berechtigungen ===
    is_active = Column(Boolean, default=True)  # Account aktiv/deaktiviert
    is_admin = Column(Boolean, default=False)  # Admin-Rechte ja/nein
    
    # === Zeitstempel (werden automatisch gesetzt) ===
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Erstelldatum
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())  # Letztes Update
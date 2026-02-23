# database.py – Datenbankverbindung und Session-Management
# Stellt die Verbindung zur SQLite-Datenbank her und verwaltet Sitzungen

from sqlalchemy import create_engine  # Erstellt die DB-Verbindung
from sqlalchemy.orm import sessionmaker, DeclarativeBase  # ORM-Werkzeuge
from app.core.config import get_settings  # Unsere App-Einstellungen

# Settings laden (enthält u.a. die DATABASE_URL)
settings = get_settings()

# Engine = die eigentliche Verbindung zur Datenbank
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False}  # Nur für SQLite nötig (erlaubt mehrere Threads)
)

# SessionLocal = Fabrik die neue Datenbank-Sitzungen erstellt
# Jeder API-Request bekommt seine eigene Sitzung
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Basisklasse für alle Datenbank-Modelle (Tabellen).
    Jedes Model (User, Post, etc.) erbt von dieser Klasse."""
    pass


def get_db():
    """Dependency für FastAPI – öffnet eine DB-Sitzung pro Request
    und schliesst sie danach automatisch wieder.
    
    Verwendung in Routers:
        def my_endpoint(db: Session = Depends(get_db)):
    """
    db = SessionLocal()  # Neue Sitzung öffnen
    try:
        yield db  # Sitzung dem Request zur Verfügung stellen
    finally:
        db.close()  # Nach dem Request immer sauber schliessen
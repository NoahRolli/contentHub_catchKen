# main.py – Einstiegspunkt der catchKen Content Hub App
# Hier wird die FastAPI-App erstellt und konfiguriert
# Server starten mit: uvicorn app.main:app --reload

from fastapi import FastAPI, Request  # Web-Framework + Request-Objekt für Templates
from fastapi.staticfiles import StaticFiles  # Stellt CSS/JS/Bilder bereit
from fastapi.templating import Jinja2Templates  # Rendert HTML-Templates
from app.core.config import get_settings  # Unsere App-Einstellungen aus .env
from app.core.database import engine, Base  # DB-Engine und Basisklasse
import app.models  # Alle Modelle laden (damit Base sie kennt)
import os
from app.routers.student_success import router as success_router  # Erfolgs-Posts Endpunkte
from app.routers.training_data import router as training_router  # Trainingsdaten Endpunkte
from app.routers.scheduled_post import router as calendar_router
from app.routers.theory import router as theory_router



# Datenbank-Tabellen erstellen (wenn sie noch nicht existieren)
# Wird bei jedem Serverstart geprüft – erstellt nur fehlende Tabellen
Base.metadata.create_all(bind=engine)

# Settings laden
settings = get_settings()

# FastAPI-App erstellen mit Metadaten (sichtbar unter /docs)
app = FastAPI(
    title=settings.app_name,  # Name in der API-Dokumentation
    description="Social media content planner for catchKen",
    version="0.1.0"  # Aktuelle Version – passen wir pro Phase an
)

# Statische Dateien verfügbar machen (CSS, JS, Bilder)
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Uploads als statische Dateien verfügbar machen (für Bild-Vorschauen im Browser)
# Ordner wird erstellt falls noch nicht vorhanden
os.makedirs("local_media/uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="local_media/uploads"), name="uploads")

# Template-Engine konfigurieren – rendert HTML-Seiten mit dynamischen Daten
templates = Jinja2Templates(directory="frontend/templates")

# === Router registrieren ===
app.include_router(success_router)  # Erfolgs-Posts unter /api/success/
app.include_router(training_router)  # Trainingsdaten unter /api/training-data/
app.include_router(calendar_router)
app.include_router(theory_router)  # Theorie-Posts unter /api/theory/


# === API Endpunkte (Routes) ===

@app.get("/")  # GET-Request auf die Startseite
async def root(request: Request):
    """Startseite – zeigt das Frontend mit Formular und Post-Liste."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")  # Health-Check Endpunkt
async def health_check():
    """Wird genutzt um zu prüfen ob der Server läuft.
    Nützlich für Monitoring und spätere Deployment-Checks."""
    return {"status": "healthy"}

@app.get("/calendar")
async def calendar_page(request: Request):
    """Kalender-Ansicht für die Content-Planung."""
    return templates.TemplateResponse("calendar.html", {"request": request})


@app.get("/theory")
async def theory_page(request: Request):
    """Theorie-Posts Seite."""
    return templates.TemplateResponse("theory.html", {"request": request})


@app.get("/training")
async def training_page(request: Request):
    """Trainingsdaten-Verwaltung."""
    return templates.TemplateResponse("training.html", {"request": request})
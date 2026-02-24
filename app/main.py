# main.py – Einstiegspunkt der catchKen Content Hub App
# Hier wird die FastAPI-App erstellt und konfiguriert
# Server starten mit: uvicorn app.main:app --reload

from fastapi import FastAPI  # Das Web-Framework
from fastapi.staticfiles import StaticFiles  # Stellt CSS/JS/Bilder bereit
from fastapi.templating import Jinja2Templates  # Rendert HTML-Templates
from app.core.config import get_settings  # Unsere App-Einstellungen aus .env

# Settings laden
settings = get_settings()

# FastAPI-App erstellen mit Metadaten (sichtbar unter /docs)
app = FastAPI(
    title=settings.app_name,  # Name in der API-Dokumentation
    description="Social media content planner for Swiss driving schools",
    version="0.1.0"  # Aktuelle Version – passen wir pro Phase an
)

# Statische Dateien verfügbar machen (CSS, JS, Bilder)
# URL /static/css/style.css → Datei frontend/static/css/style.css
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Template-Engine konfigurieren – rendert HTML-Seiten mit dynamischen Daten
templates = Jinja2Templates(directory="frontend/templates")


# === API Endpunkte (Routes) ===

@app.get("/")  # GET-Request auf die Startseite
async def root():
    """Startseite – zeigt den aktuellen Status der App als JSON."""
    return {
        "app": settings.app_name,
        "status": "running",
        "phase": "1 - Foundation"
    }


@app.get("/health")  # Health-Check Endpunkt
async def health_check():
    """Wird genutzt um zu prüfen ob der Server läuft.
    Nützlich für Monitoring und spätere Deployment-Checks."""
    return {"status": "healthy"}
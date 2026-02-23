# config.py – Zentrale Konfiguration der App
# Liest Einstellungen aus der .env Datei und stellt sie der App zur Verfügung

from pydantic_settings import BaseSettings  # Bibliothek für typisierte Settings
from functools import lru_cache  # Cache-Dekorator (lädt Settings nur einmal)


class Settings(BaseSettings):
    """Alle Einstellungen der App – Werte kommen aus .env oder den Defaults hier."""
    
    # Allgemein
    app_name: str = "catchKen Content Hub"
    app_env: str = "development"  # development / production
    database_url: str = "sqlite:///./catchken.db"  # Pfad zur SQLite-Datenbank
    secret_key: str = "change-me-to-random-string"  # Für spätere Auth/Sicherheit
    
    # LLM-Einstellungen
    ollama_base_url: str = "http://localhost:11434"  # Lokaler Ollama Server
    openai_api_key: str = ""  # Fallback – nur wenn Ollama nicht reicht
    
    # Dateipfade
    media_path: str = "media/uploads"  # Wo Uploads gespeichert werden (SSD via Symlink)
    
    class Config:
        env_file = ".env"  # Sagt pydantic: lies die .env Datei im Projektroot


@lru_cache()  # Cached das Ergebnis – Settings werden nur 1x geladen, nicht bei jedem Aufruf
def get_settings():
    """Gibt die App-Settings zurück. Wird überall im Projekt importiert."""
    return Settings()
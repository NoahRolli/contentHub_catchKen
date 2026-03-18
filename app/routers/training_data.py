# app/routers/training_data.py
# ============================================================
# API-Endpoints für Trainingsdaten-Management.
# Hier kann man:
#   - Einzelne Trainings-Posts manuell erstellen
#   - Mehrere Posts als Bulk-Upload importieren
#   - Instagram JSON-Export importieren
#   - Alle Trainings-Posts auflisten und löschen
#   - Statistiken abrufen
# ============================================================

import json  # Zum Parsen des Instagram JSON-Exports
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session

from app.core.database import get_db  # Dependency Injection für DB-Session
from app.models.training_post import TrainingPost, Platform, ContentType
from app.schemas.training_data import (
    TrainingPostCreate,
    TrainingPostBulkUpload,
    TrainingPostResponse,
    TrainingDataStats,
    PlatformSchema,
    ContentTypeSchema,
)
from app.services.llm.training_data import get_training_data_stats


# Router mit Prefix → alle Endpoints starten mit /api/training-data
router = APIRouter(
    prefix="/api/training-data",
    tags=["Training Data"]  # Gruppierung in der Swagger-Doku (/docs)
)


# =====================================================
# POST /api/training-data/ — Einzelnen Post erstellen
# =====================================================
@router.post("/", response_model=TrainingPostResponse, status_code=201)
def create_training_post(
    post_data: TrainingPostCreate,  # Pydantic validiert automatisch
    db: Session = Depends(get_db)   # DB-Session wird injiziert
):
    """
    Erstellt einen einzelnen Trainings-Post.
    Für manuelles Eingeben über Formular oder API.
    """
    # Pydantic-Schema → SQLAlchemy-Model umwandeln
    db_post = TrainingPost(
        platform=post_data.platform.value,         # Enum → String ("instagram")
        content_type=post_data.content_type.value,  # Enum → String ("success")
        caption=post_data.caption,
        hashtags=post_data.hashtags,
        source_url=post_data.source_url,
        original_date=post_data.original_date,
    )

    db.add(db_post)      # Zur Session hinzufügen
    db.commit()           # In DB schreiben
    db.refresh(db_post)   # Aktualisierte Daten laden (inkl. auto-generierter id + created_at)

    return db_post


# =====================================================
# POST /api/training-data/bulk — Mehrere Posts auf einmal
# =====================================================
@router.post("/bulk", response_model=list[TrainingPostResponse], status_code=201)
def bulk_upload_training_posts(
    bulk_data: TrainingPostBulkUpload,
    db: Session = Depends(get_db)
):
    """
    Bulk-Upload: Mehrere Trainings-Posts auf einmal importieren.
    Platform und Content-Type gelten für ALLE Posts im Batch.
    Ideal für CSV-Daten die vorher formatiert wurden.
    """
    created_posts = []  # Sammelt die erstellten DB-Objekte

    for item in bulk_data.posts:
        db_post = TrainingPost(
            platform=bulk_data.platform.value,       # Gleiche Plattform für alle
            content_type=bulk_data.content_type.value,  # Gleicher Typ für alle
            caption=item.caption,
            hashtags=item.hashtags,
            source_url=item.source_url,
            original_date=item.original_date,
        )
        db.add(db_post)
        created_posts.append(db_post)

    db.commit()  # Alles auf einmal committen (effizienter als einzeln)

    # Alle refreshen um auto-generierte Felder zu laden
    for post in created_posts:
        db.refresh(post)

    return created_posts


# =====================================================
# POST /api/training-data/import-instagram — Instagram JSON Import
# =====================================================
@router.post("/import-instagram", response_model=list[TrainingPostResponse], status_code=201)
async def import_instagram_json(
    file: UploadFile = File(..., description="Instagram JSON-Export Datei"),
    content_type: ContentTypeSchema = Query(
        default=ContentTypeSchema.SUCCESS,
        description="Content-Typ für alle importierten Posts"
    ),
    db: Session = Depends(get_db)
):
    """
    Importiert Posts aus einem Instagram JSON-Export.

    Instagram-Export Format (nach Download über Instagram App):
    Die Posts liegen als JSON-Array, jedes Element hat eine
    "title" (= Caption) und "creation_timestamp".

    Akzeptiert auch einfache JSON-Arrays:
    [{"caption": "...", "hashtags": "...", "date": "..."}]
    """
    # --- Datei lesen und als JSON parsen ---
    try:
        raw_content = await file.read()  # Datei-Bytes lesen
        data = json.loads(raw_content)   # JSON parsen
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Datei ist kein gültiges JSON. Bitte Instagram JSON-Export verwenden."
        )

    created_posts = []

    # --- Instagram's offizielles Export-Format verarbeiten ---
    # Instagram exportiert Posts als Liste von Objekten mit "title" und "creation_timestamp"
    if isinstance(data, list):
        for item in data:
            # Caption extrahieren — Instagram nutzt verschiedene Feldnamen
            caption = (
                item.get("title")          # Offizielles Instagram-Format
                or item.get("caption")     # Unser eigenes Format
                or item.get("text")        # Alternatives Format
                or ""
            )

            # Leere Captions überspringen (z.B. Bild-Posts ohne Text)
            if not caption or len(caption.strip()) < 5:
                continue

            # Hashtags extrahieren falls vorhanden
            hashtags = item.get("hashtags", None)

            # Wenn keine separaten Hashtags → aus Caption extrahieren
            if not hashtags:
                hashtags = _extract_hashtags_from_caption(caption)

            # Datum parsen — Instagram nutzt Unix-Timestamps
            original_date = None
            if "creation_timestamp" in item:
                # Instagram: Unix-Timestamp (Sekunden seit 1970)
                try:
                    original_date = datetime.fromtimestamp(item["creation_timestamp"])
                except (ValueError, TypeError, OSError):
                    pass  # Ungültiges Datum → ignorieren
            elif "date" in item:
                # Unser Format: ISO-String oder anderes Datumsformat
                try:
                    original_date = datetime.fromisoformat(item["date"])
                except (ValueError, TypeError):
                    pass

            # Post-URL falls vorhanden
            source_url = item.get("url") or item.get("source_url") or None

            # DB-Objekt erstellen
            db_post = TrainingPost(
                platform=Platform.INSTAGRAM,
                content_type=content_type.value,
                caption=caption.strip(),
                hashtags=hashtags,
                source_url=source_url,
                original_date=original_date,
            )
            db.add(db_post)
            created_posts.append(db_post)

    else:
        raise HTTPException(
            status_code=400,
            detail="Erwartetes Format: JSON-Array (Liste von Posts). "
                   "Bitte prüfe das Export-Format."
        )

    # Alles auf einmal committen
    if created_posts:
        db.commit()
        for post in created_posts:
            db.refresh(post)

    return created_posts


# =====================================================
# GET /api/training-data/ — Alle Trainings-Posts auflisten
# =====================================================
@router.get("/", response_model=list[TrainingPostResponse])
def list_training_posts(
    platform: PlatformSchema | None = Query(default=None, description="Nach Plattform filtern"),
    content_type: ContentTypeSchema | None = Query(default=None, description="Nach Content-Typ filtern"),
    limit: int = Query(default=50, ge=1, le=500, description="Max Anzahl Ergebnisse"),
    db: Session = Depends(get_db)
):
    """
    Listet alle Trainings-Posts auf, optional gefiltert nach Plattform und Typ.
    Sortiert nach Erstellungsdatum (neueste zuerst).
    """
    # Query starten
    query = db.query(TrainingPost)

    # Optionale Filter anwenden (nur wenn Parameter gesetzt)
    if platform:
        query = query.filter(TrainingPost.platform == platform.value)
    if content_type:
        query = query.filter(TrainingPost.content_type == content_type.value)

    # Sortieren und limitieren
    posts = (
        query
        .order_by(TrainingPost.created_at.desc())  # Neueste zuerst
        .limit(limit)
        .all()
    )

    return posts


# =====================================================
# GET /api/training-data/stats — Statistik-Übersicht
# =====================================================
@router.get("/stats", response_model=TrainingDataStats)
def get_stats(db: Session = Depends(get_db)):
    """
    Gibt Statistiken über die vorhandenen Trainingsdaten zurück.
    z.B. "12 Instagram-Posts, 3 TikTok-Posts, neuester Post: 15.03.2025"
    """
    return get_training_data_stats(db)


# =====================================================
# DELETE /api/training-data/{post_id} — Einzelnen Post löschen
# =====================================================
@router.delete("/{post_id}", status_code=204)
def delete_training_post(
    post_id: int,
    db: Session = Depends(get_db)
):
    """Löscht einen einzelnen Trainings-Post anhand seiner ID."""
    post = db.query(TrainingPost).filter(TrainingPost.id == post_id).first()

    if not post:
        raise HTTPException(status_code=404, detail=f"Training Post {post_id} nicht gefunden")

    db.delete(post)
    db.commit()

    # 204 No Content → kein Response Body nötig
    return None


# =====================================================
# DELETE /api/training-data/ — Alle Posts einer Kategorie löschen
# =====================================================
@router.delete("/", status_code=200)
def delete_all_training_posts(
    platform: PlatformSchema | None = Query(default=None),
    content_type: ContentTypeSchema | None = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Löscht alle Trainings-Posts, optional gefiltert.
    Ohne Filter → ALLE Trainings-Posts werden gelöscht!
    Gibt die Anzahl gelöschter Posts zurück.
    """
    query = db.query(TrainingPost)

    if platform:
        query = query.filter(TrainingPost.platform == platform.value)
    if content_type:
        query = query.filter(TrainingPost.content_type == content_type.value)

    # .delete() gibt die Anzahl gelöschter Rows zurück
    deleted_count = query.delete()
    db.commit()

    return {"deleted": deleted_count, "message": f"{deleted_count} Trainings-Posts gelöscht"}


# =====================================================
# HILFSFUNKTION (privat)
# =====================================================

def _extract_hashtags_from_caption(caption: str) -> str | None:
    """
    Extrahiert Hashtags aus einer Caption.
    Instagram-Posts haben die Hashtags oft am Ende der Caption.

    Sucht nach Wörtern die mit # beginnen und gibt sie als
    zusammenhängenden String zurück.

    Args:
        caption: Die Instagram-Caption

    Returns:
        String mit allen Hashtags oder None wenn keine gefunden
    """
    # Alle Wörter finden die mit # beginnen
    words = caption.split()
    hashtags = [word for word in words if word.startswith("#")]

    if hashtags:
        return " ".join(hashtags)  # z.B. "#fahrschule #bestanden #catchken"

    return None
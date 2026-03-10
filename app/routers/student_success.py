# student_success.py – API-Endpunkte für Erfolgs-Posts
# Stellt CRUD-Operationen bereit: Erstellen, Lesen, Bearbeiten, Löschen
# Alle Endpunkte sind unter /api/success/ erreichbar

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form  # FastAPI-Werkzeuge
from sqlalchemy.orm import Session  # Datenbank-Sitzung
from typing import Optional  # Für optionale Parameter
from datetime import date  # Für Datumsfelder
import shutil  # Für Dateioperationen (Bild-Upload)
import os  # Für Pfad-Operationen
import uuid  # Für eindeutige Dateinamen

from app.core.database import get_db  # DB-Session pro Request
from app.core.config import get_settings  # App-Einstellungen
from app.models.student_success_post import StudentSuccessPost  # Datenbank-Modell
from app.schemas.student_success import (  # Pydantic Schemas
    StudentSuccessResponse,
    StudentSuccessUpdate,
    StudentSuccessListResponse,
)

# Router erstellen – alle Endpunkte hier starten mit /api/success
router = APIRouter(
    prefix="/api/success",  # URL-Präfix für alle Endpunkte
    tags=["Erfolgs-Posts"],  # Gruppierung in der API-Dokumentation (/docs)
)

# Settings laden (für Dateipfade)
settings = get_settings()


@router.post("/", response_model=StudentSuccessResponse)  # POST /api/success/
async def create_success_post(
    exam_date: date = Form(..., description="Prüfungsdatum"),  # Pflichtfeld
    consent_given: bool = Form(..., description="Einverständnis Bildnutzung"),  # Pflichtfeld
    category: str = Form("B", description="Führerschein-Kategorie"),  # Default: B
    student_name: Optional[str] = Form(None, description="Vorname (optional)"),  # Optional
    image: Optional[UploadFile] = File(None, description="Bild-Upload (optional)"),  # Optional
    db: Session = Depends(get_db),  # Datenbank-Session (wird automatisch injiziert)
):
    """Erstellt einen neuen Erfolgs-Post.
    
    1. Prüft ob Consent gegeben wurde (Pflicht!)
    2. Speichert optional das Bild auf der SSD
    3. Erstellt den Datenbank-Eintrag mit Status 'draft'
    """
    
    # Consent ist Pflicht – ohne geht nichts
    if not consent_given:
        raise HTTPException(
            status_code=400,  # Bad Request
            detail="Einverständnis für Bildnutzung ist Pflicht (consent_given muss True sein)"
        )
    
    # Bild speichern (falls hochgeladen)
    image_path = None
    if image:
        # Eindeutigen Dateinamen generieren (verhindert Überschreibungen)
        file_extension = os.path.splitext(image.filename)[1]  # z.B. ".jpg"
        unique_filename = f"{uuid.uuid4()}{file_extension}"  # z.B. "a1b2c3d4.jpg"
        
        # Zielordner erstellen falls nicht vorhanden
        upload_dir = os.path.join(settings.media_path, "success")
        os.makedirs(upload_dir, exist_ok=True)  # Erstellt Ordner rekursiv
        
        # Datei auf SSD speichern
        file_path = os.path.join(upload_dir, unique_filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)  # Kopiert Upload in Datei
        
        image_path = file_path  # Pfad für Datenbank merken
    
    # Datenbank-Eintrag erstellen
    db_post = StudentSuccessPost(
        user_id=1,  # TODO: Phase 2b – echten User aus Auth nehmen
        student_name=student_name,
        exam_date=exam_date,
        category=category,
        consent_given=consent_given,
        image_path=image_path,
        status="draft",  # Neue Posts starten immer als Draft
    )
    
    db.add(db_post)  # Zur Sitzung hinzufügen
    db.commit()  # In Datenbank schreiben
    db.refresh(db_post)  # Aktualisierte Daten laden (inkl. auto-generierter ID)
    
    return db_post  # Pydantic konvertiert automatisch dank from_attributes=True


@router.get("/", response_model=StudentSuccessListResponse)  # GET /api/success/
async def list_success_posts(
    skip: int = 0,  # Wie viele Posts überspringen (für Pagination)
    limit: int = 20,  # Wie viele Posts laden (max pro Seite)
    status: Optional[str] = None,  # Optional filtern nach Status
    db: Session = Depends(get_db),
):
    """Listet alle Erfolgs-Posts auf.
    
    Unterstützt Pagination (skip/limit) und Filter nach Status.
    Sortiert nach Erstelldatum (neueste zuerst).
    """
    
    # Basis-Query: alle Posts, neueste zuerst
    query = db.query(StudentSuccessPost).order_by(StudentSuccessPost.created_at.desc())
    
    # Optional nach Status filtern (draft/ready/published)
    if status:
        query = query.filter(StudentSuccessPost.status == status)
    
    # Gesamtanzahl für Pagination
    total = query.count()
    
    # Posts mit Pagination laden
    posts = query.offset(skip).limit(limit).all()
    
    return StudentSuccessListResponse(total=total, posts=posts)


@router.get("/{post_id}", response_model=StudentSuccessResponse)  # GET /api/success/5
async def get_success_post(
    post_id: int,  # ID aus der URL
    db: Session = Depends(get_db),
):
    """Lädt einen einzelnen Erfolgs-Post anhand seiner ID."""
    
    # Post in Datenbank suchen
    post = db.query(StudentSuccessPost).filter(StudentSuccessPost.id == post_id).first()
    
    # Wenn nicht gefunden: 404 Fehler
    if not post:
        raise HTTPException(
            status_code=404,
            detail=f"Erfolgs-Post mit ID {post_id} nicht gefunden"
        )
    
    return post


@router.put("/{post_id}", response_model=StudentSuccessResponse)  # PUT /api/success/5
async def update_success_post(
    post_id: int,  # ID aus der URL
    update_data: StudentSuccessUpdate,  # Neue Daten als JSON Body
    db: Session = Depends(get_db),
):
    """Aktualisiert einen bestehenden Erfolgs-Post.
    
    Nur die mitgeschickten Felder werden geändert (Partial Update).
    So kann der Admin z.B. nur die Caption ändern ohne alles neu zu schicken.
    """
    
    # Post suchen
    post = db.query(StudentSuccessPost).filter(StudentSuccessPost.id == post_id).first()
    
    if not post:
        raise HTTPException(status_code=404, detail=f"Erfolgs-Post mit ID {post_id} nicht gefunden")
    
    # Nur Felder aktualisieren die tatsächlich mitgeschickt wurden
    update_dict = update_data.model_dump(exclude_unset=True)  # Nur gesetzte Felder
    for field, value in update_dict.items():
        setattr(post, field, value)  # Feld auf dem DB-Objekt setzen
    
    db.commit()  # Änderungen speichern
    db.refresh(post)  # Aktualisierte Daten laden
    
    return post


@router.delete("/{post_id}")  # DELETE /api/success/5
async def delete_success_post(
    post_id: int,
    db: Session = Depends(get_db),
):
    """Löscht einen Erfolgs-Post und sein zugehöriges Bild.
    
    Achtung: Unwiderruflich! Löscht sowohl den DB-Eintrag als auch die Bilddatei.
    """
    
    # Post suchen
    post = db.query(StudentSuccessPost).filter(StudentSuccessPost.id == post_id).first()
    
    if not post:
        raise HTTPException(status_code=404, detail=f"Erfolgs-Post mit ID {post_id} nicht gefunden")
    
    # Bild von SSD löschen (falls vorhanden)
    if post.image_path and os.path.exists(post.image_path):
        os.remove(post.image_path)
    
    # DB-Eintrag löschen
    db.delete(post)
    db.commit()
    
    return {"message": f"Erfolgs-Post {post_id} gelöscht", "deleted_id": post_id}
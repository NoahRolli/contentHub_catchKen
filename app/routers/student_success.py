# student_success.py – API-Endpunkte für Erfolgs-Posts
# Stellt CRUD-Operationen bereit: Erstellen, Lesen, Bearbeiten, Löschen
# Alle Endpunkte sind unter /api/success/ erreichbar
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form  # FastAPI-Werkzeuge
from sqlalchemy.orm import Session  # Datenbank-Sitzung
from typing import Optional, List  # Für optionale und Listen-Parameter
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
    GenerateContentRequest,    # NEU: Request-Schema für Generierung
    GenerateContentResponse,   # NEU: Response-Schema für Generierung
)
from app.services.llm import get_llm_provider, get_training_examples, has_training_data  # NEU: LLM Service
# Router erstellen – alle Endpunkte hier starten mit /api/success
router = APIRouter(
    prefix="/api/success",  # URL-Präfix für alle Endpunkte
    tags=["Erfolgs-Posts"],  # Gruppierung in der API-Dokumentation (/docs)
)
# Settings laden (für Dateipfade)
settings = get_settings()
@router.post("/", response_model=StudentSuccessResponse)  # POST /api/success/
async def create_success_post(
    exam_date: date = Form(...),
    consent_given: bool = Form(...),
    category: str = Form("B"),
    student_name: Optional[str] = Form(None),
    details: Optional[str] = Form(None),           # Zusatzinfos für LLM
    images: List[UploadFile] = File(default=[]),    # Mehrere Bilder möglich
    db: Session = Depends(get_db),
):
    """Erstellt einen neuen Erfolgs-Post mit optionalen Bildern und Details."""

    if not consent_given:
        raise HTTPException(status_code=400, detail="Einverständnis für Bildnutzung ist Pflicht")

    # Alle hochgeladenen Bilder speichern
    image_path = None    # Erstes Bild (Rückwärtskompatibilität)
    saved_paths = []     # Alle Bilder als Liste

    for img in images:
        if img.filename:  # Leere File-Inputs überspringen
            ext = os.path.splitext(img.filename)[1]
            unique_name = f"{uuid.uuid4()}{ext}"
            upload_dir = os.path.join(settings.media_path, "success")
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, unique_name)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(img.file, buffer)
            saved_paths.append(file_path)
            if image_path is None:
                image_path = file_path  # Erstes Bild für Rückwärtskompatibilität

    # Datenbank-Eintrag erstellen
    db_post = StudentSuccessPost(
        user_id=1,  # TODO: Phase 2b – echten User aus Auth
        student_name=student_name,
        exam_date=exam_date,
        category=category,
        consent_given=consent_given,
        image_path=image_path,
        image_paths=saved_paths if saved_paths else None,
        details=details,
        status="draft",
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


# =====================================================
# POST /api/success/{post_id}/generate — Content generieren
# =====================================================
@router.post("/{post_id}/generate", response_model=GenerateContentResponse)
async def generate_content(
    post_id: int,
    request_data: GenerateContentRequest = None,  # Optional: extra Details mitgeben
    db: Session = Depends(get_db),
):
    """Generiert Instagram Caption + Hashtags und TikTok-Beschreibung für einen Erfolgs-Post.
    
    Flow:
        1. Post aus DB laden (braucht student_name + category)
        2. Prüfen ob Trainingsdaten vorhanden sind
        3. Wenn ja → Few-Shot Prompt mit Beispielen
        4. Wenn nein → Generischer Prompt
        5. LLM aufrufen (Ollama oder OpenAI)
        6. Ergebnis zurückgeben (noch NICHT gespeichert!)
        
    Der Admin sieht den generierten Text, kann ihn anpassen,
    und speichert erst dann über PUT /api/success/{post_id}.
    """
    
    # --- 1. Post aus DB laden ---
    post = db.query(StudentSuccessPost).filter(StudentSuccessPost.id == post_id).first()
    
    if not post:
        raise HTTPException(status_code=404, detail=f"Erfolgs-Post mit ID {post_id} nicht gefunden")
    
    # --- 2. Request-Daten vorbereiten ---
    # Falls kein Body mitgeschickt wurde → Defaults verwenden
    if request_data is None:
        request_data = GenerateContentRequest()
    
    # Student Name: Aus Post nehmen, oder "Fahrschüler/in" als Fallback
    student_name = post.student_name or "Fahrschüler/in"
    
    # Exam Type: Kategorie in lesbaren Text umwandeln
    category_map = {
        "B": "Autoprüfung (Kat. B)",
        "A": "Motorradprüfung (Kat. A)",
        "A1": "Motorradprüfung (Kat. A1)",
        "BE": "Anhängerprüfung (Kat. BE)",
    }
    exam_type = category_map.get(post.category, f"Fahrprüfung (Kat. {post.category})")
    
    # --- 3. Trainingsdaten laden (wenn gewünscht) ---
    training_examples_ig = []  # Instagram Beispiele
    training_examples_tt = []  # TikTok Beispiele
    
    if request_data.use_training_data:
        # Instagram-Beispiele laden
        training_examples_ig = get_training_examples(
            db=db,
            platform="instagram",
            content_type="success"
        )
        # TikTok-Beispiele laden
        training_examples_tt = get_training_examples(
            db=db,
            platform="tiktok",
            content_type="success"
        )
    
    # --- 4. LLM Provider holen ---
    provider = get_llm_provider()
    
    # Health Check: Ist der Provider erreichbar?
    is_healthy = await provider.health_check()
    if not is_healthy:
        raise HTTPException(
            status_code=503,  # Service Unavailable
            detail=f"LLM Provider '{provider.get_provider_name()}' ist nicht erreichbar. "
                   f"Ist Ollama gestartet? (ollama serve)"
        )
    
    # --- 5. Instagram Caption generieren ---
    try:
        ig_result = await provider.generate_instagram_caption(
            student_name=student_name,
            exam_type=exam_type,
            details=request_data.details or post.details,  # Request-Details haben Vorrang, sonst gespeicherte
            training_examples=training_examples_ig if training_examples_ig else None
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Fehler bei Instagram-Generierung: {str(e)}"
        )
    
    # --- 6. TikTok Beschreibung generieren ---
    try:
        tt_result = await provider.generate_tiktok_description(
            student_name=student_name,
            exam_type=exam_type,
            details=request_data.details or post.details,
            training_examples=training_examples_tt if training_examples_tt else None
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Fehler bei TikTok-Generierung: {str(e)}"
        )
    
    # --- 7. Ergebnis zurückgeben (noch NICHT in DB gespeichert!) ---
    return GenerateContentResponse(
        instagram_caption=ig_result["caption"],
        tiktok_description=tt_result["description"],
        provider=provider.get_provider_name(),
        used_training_data=len(training_examples_ig) > 0 or len(training_examples_tt) > 0,
        training_examples_count=max(len(training_examples_ig), len(training_examples_tt))
    )


# =====================================================
# POST /api/success/{post_id}/apply-generated — Generierten Content speichern
# =====================================================
@router.post("/{post_id}/apply-generated", response_model=StudentSuccessResponse)
async def apply_generated_content(
    post_id: int,
    caption: str = Form(..., description="Instagram Post-Text (Caption + Hashtags, vom Admin geprüft)"),
    story_text: str = Form(None, description="TikTok-Beschreibung inkl. Hashtags"),
    db: Session = Depends(get_db),
):
    """Speichert den generierten (und ggf. angepassten) Content auf dem Post.

    Caption enthält den vollständigen Instagram-Text inkl. Hashtags.
    """

    post = db.query(StudentSuccessPost).filter(StudentSuccessPost.id == post_id).first()

    if not post:
        raise HTTPException(status_code=404, detail=f"Erfolgs-Post mit ID {post_id} nicht gefunden")

    # Generierten Text speichern (Caption = voller Post-Text, Hashtags separat nicht mehr nötig)
    post.caption = caption
    post.story_text = story_text

    db.commit()
    db.refresh(post)

    return post
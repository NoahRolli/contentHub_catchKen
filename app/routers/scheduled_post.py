# app/routers/scheduled_post.py
# ============================================================
# API-Endpoints für den Kalender / Scheduling.
# Stellt CRUD bereit plus spezielle Kalender-Endpoints:
#   - Range-Query: Alle Posts zwischen Datum A und B
#   - Move: Drag & Drop (nur Datum ändern)
#   - Unplanned: Posts ohne Datum (Sidebar)
# ============================================================

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.scheduled_post import ScheduledPost
from app.schemas.scheduled_post import (
    ScheduledPostCreate,
    ScheduledPostUpdate,
    ScheduledPostMove,
    ScheduledPostResponse,
)

router = APIRouter(
    prefix="/api/calendar",
    tags=["Kalender"],
)


# === POST /api/calendar/ — Neuen Eintrag erstellen ===
@router.post("/", response_model=ScheduledPostResponse, status_code=201)
async def create_scheduled_post(
    post_data: ScheduledPostCreate,
    db: Session = Depends(get_db),
):
    """Erstellt einen neuen Kalender-Eintrag."""
    db_post = ScheduledPost(
        user_id=1,  # TODO: Aus Auth nehmen
        content_type=post_data.content_type.value,
        scheduled_date=post_data.scheduled_date,
        scheduled_time=post_data.scheduled_time,
        platform=post_data.platform.value,
        caption=post_data.caption,
        hashtags=post_data.hashtags,
        story_text=post_data.story_text,
        notes=post_data.notes,
        status="draft",
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


# === GET /api/calendar/range — Posts in einem Datumsbereich ===
@router.get("/range", response_model=list[ScheduledPostResponse])
async def get_posts_in_range(
    start: date = Query(..., description="Startdatum (inklusiv)"),
    end: date = Query(..., description="Enddatum (inklusiv)"),
    db: Session = Depends(get_db),
):
    """Lädt alle Kalender-Einträge zwischen start und end.
    Wird vom Frontend für Wochen-/Monatsansicht genutzt."""
    posts = (
        db.query(ScheduledPost)
        .filter(
            ScheduledPost.scheduled_date >= start,
            ScheduledPost.scheduled_date <= end,
        )
        .order_by(ScheduledPost.scheduled_date, ScheduledPost.scheduled_time)
        .all()
    )
    return posts


# === GET /api/calendar/{post_id} — Einzelnen Eintrag laden ===
@router.get("/{post_id}", response_model=ScheduledPostResponse)
async def get_scheduled_post(
    post_id: int,
    db: Session = Depends(get_db),
):
    """Lädt einen einzelnen Kalender-Eintrag."""
    post = db.query(ScheduledPost).filter(ScheduledPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail=f"Kalender-Eintrag {post_id} nicht gefunden")
    return post


# === PUT /api/calendar/{post_id} — Eintrag bearbeiten ===
@router.put("/{post_id}", response_model=ScheduledPostResponse)
async def update_scheduled_post(
    post_id: int,
    update_data: ScheduledPostUpdate,
    db: Session = Depends(get_db),
):
    """Aktualisiert einen Kalender-Eintrag (Partial Update)."""
    post = db.query(ScheduledPost).filter(ScheduledPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail=f"Kalender-Eintrag {post_id} nicht gefunden")

    # Nur gesetzte Felder updaten
    update_dict = update_data.model_dump(exclude_unset=True)
    # Enums zu Strings konvertieren für DB
    for field, value in update_dict.items():
        if hasattr(value, "value"):
            value = value.value
        setattr(post, field, value)

    db.commit()
    db.refresh(post)
    return post


# === PATCH /api/calendar/{post_id}/move — Drag & Drop ===
@router.patch("/{post_id}/move", response_model=ScheduledPostResponse)
async def move_scheduled_post(
    post_id: int,
    move_data: ScheduledPostMove,
    db: Session = Depends(get_db),
):
    """Verschiebt einen Post auf ein neues Datum (Drag & Drop)."""
    post = db.query(ScheduledPost).filter(ScheduledPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail=f"Kalender-Eintrag {post_id} nicht gefunden")

    post.scheduled_date = move_data.scheduled_date
    db.commit()
    db.refresh(post)
    return post


# === DELETE /api/calendar/{post_id} — Eintrag löschen ===
@router.delete("/{post_id}", status_code=204)
async def delete_scheduled_post(
    post_id: int,
    db: Session = Depends(get_db),
):
    """Löscht einen Kalender-Eintrag."""
    post = db.query(ScheduledPost).filter(ScheduledPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail=f"Kalender-Eintrag {post_id} nicht gefunden")

    db.delete(post)
    db.commit()
    return None
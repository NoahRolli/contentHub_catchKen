# app/routers/theory.py
# API-Endpoints für Theorie-Posts
# CRUD + LLM-Generierung für Fahrschultheorie als Social-Media-Content

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.theory_post import TheoryPost
from app.schemas.theory_post import (
    TheoryPostCreate,
    TheoryPostUpdate,
    TheoryPostResponse,
    TheoryPostListResponse,
    TheoryGenerateResponse,
)
from app.services.llm import get_llm_provider, get_training_examples, has_training_data
from app.services.llm.prompts import (
    build_theory_instagram_prompt,
    build_theory_tiktok_prompt,
    parse_instagram_response,
    parse_tiktok_response,
)

router = APIRouter(
    prefix="/api/theory",
    tags=["Theorie-Posts"],
)


# === POST /api/theory/ — Neuen Theorie-Post erstellen ===
@router.post("/", response_model=TheoryPostResponse, status_code=201)
async def create_theory_post(
    post_data: TheoryPostCreate,
    db: Session = Depends(get_db),
):
    """Erstellt einen neuen Theorie-Post."""
    db_post = TheoryPost(
        topic=post_data.topic,
        content=post_data.content,
        source=post_data.source,
        status="draft",
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


# === GET /api/theory/ — Alle Theorie-Posts listen ===
@router.get("/", response_model=TheoryPostListResponse)
async def list_theory_posts(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """Alle Theorie-Posts, neueste zuerst."""
    query = db.query(TheoryPost).order_by(TheoryPost.created_at.desc())
    total = query.count()
    posts = query.offset(skip).limit(limit).all()
    return TheoryPostListResponse(total=total, posts=posts)


# === GET /api/theory/{id} — Einzelner Theorie-Post ===
@router.get("/{post_id}", response_model=TheoryPostResponse)
async def get_theory_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(TheoryPost).filter(TheoryPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Theorie-Post nicht gefunden")
    return post


# === PUT /api/theory/{id} — Theorie-Post bearbeiten ===
@router.put("/{post_id}", response_model=TheoryPostResponse)
async def update_theory_post(
    post_id: int,
    update_data: TheoryPostUpdate,
    db: Session = Depends(get_db),
):
    """Partial Update — nur gesetzte Felder werden geändert."""
    post = db.query(TheoryPost).filter(TheoryPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Theorie-Post nicht gefunden")

    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(post, field, value)

    db.commit()
    db.refresh(post)
    return post


# === DELETE /api/theory/{id} — Theorie-Post löschen ===
@router.delete("/{post_id}")
async def delete_theory_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(TheoryPost).filter(TheoryPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Theorie-Post nicht gefunden")
    db.delete(post)
    db.commit()
    return {"message": f"Theorie-Post {post_id} gelöscht"}


# === POST /api/theory/{id}/generate — LLM-Generierung ===
@router.post("/{post_id}/generate", response_model=TheoryGenerateResponse)
async def generate_theory_content(post_id: int, db: Session = Depends(get_db)):
    """Generiert Instagram + TikTok Content für einen Theorie-Post."""

    post = db.query(TheoryPost).filter(TheoryPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Theorie-Post nicht gefunden")

    # Trainingsdaten laden (content_type="theory")
    training_ig = get_training_examples(db=db, platform="instagram", content_type="theory")
    training_tt = get_training_examples(db=db, platform="tiktok", content_type="theory")

    # LLM Provider
    provider = get_llm_provider()
    is_healthy = await provider.health_check()
    if not is_healthy:
        raise HTTPException(status_code=503, detail="LLM Provider nicht erreichbar")

    # Prompts bauen und LLM aufrufen
    ig_prompt = build_theory_instagram_prompt(
        topic=post.topic,
        content=post.content,
        training_examples=training_ig if training_ig else None,
    )
    tt_prompt = build_theory_tiktok_prompt(
        topic=post.topic,
        content=post.content,
        training_examples=training_tt if training_tt else None,
    )

    try:
        ig_raw = await provider._call_ollama(ig_prompt)
        ig_result = parse_instagram_response(ig_raw)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Instagram-Generierung: {str(e)}")

    try:
        tt_raw = await provider._call_ollama(tt_prompt)
        tt_result = parse_tiktok_response(tt_raw)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TikTok-Generierung: {str(e)}")

    return TheoryGenerateResponse(
        instagram_caption=ig_result["caption"],
        tiktok_description=tt_result["description"],
        provider=provider.get_provider_name(),
        used_training_data=len(training_ig) > 0 or len(training_tt) > 0,
        training_examples_count=max(len(training_ig), len(training_tt)),
    )


# === POST /api/theory/{id}/apply-generated — Generierten Content speichern ===
@router.post("/{post_id}/apply-generated", response_model=TheoryPostResponse)
async def apply_generated_theory(
    post_id: int,
    update_data: TheoryPostUpdate,
    db: Session = Depends(get_db),
):
    """Speichert den generierten Content auf dem Theorie-Post."""
    post = db.query(TheoryPost).filter(TheoryPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Theorie-Post nicht gefunden")

    if update_data.caption is not None:
        post.caption = update_data.caption
    if update_data.story_text is not None:
        post.story_text = update_data.story_text

    db.commit()
    db.refresh(post)
    return post

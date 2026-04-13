# app/routers/news.py
# API-Endpoints für RSS-News: Quellen verwalten, scannen, Posts generieren

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.content_source import ContentSource
from app.models.news_item import NewsItem
from app.schemas.news import (
    ContentSourceCreate,
    ContentSourceResponse,
    NewsItemResponse,
    ScanResult,
    NewsGenerateResponse,
)
from app.services.rss_scanner import scan_feed, scan_all_active_feeds
from app.services.llm import get_llm_provider, get_training_examples
from app.services.llm.prompts import (
    build_news_instagram_prompt,
    build_news_tiktok_prompt,
    parse_instagram_response,
    parse_tiktok_response,
)

router = APIRouter(
    prefix="/api/news",
    tags=["News"],
)


# =====================================================
# Quellen verwalten
# =====================================================

@router.post("/sources", response_model=ContentSourceResponse, status_code=201)
async def create_source(data: ContentSourceCreate, db: Session = Depends(get_db)):
    """Neue RSS-Quelle hinzufügen."""
    source = ContentSource(
        name=data.name,
        source_type="rss",
        url=data.url,
        keywords=data.keywords,
        scan_interval=data.scan_interval,
        is_active=True,
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@router.get("/sources", response_model=list[ContentSourceResponse])
async def list_sources(db: Session = Depends(get_db)):
    """Alle RSS-Quellen auflisten."""
    return db.query(ContentSource).order_by(ContentSource.created_at.desc()).all()


@router.delete("/sources/{source_id}")
async def delete_source(source_id: int, db: Session = Depends(get_db)):
    """RSS-Quelle löschen (inkl. zugehöriger News-Items)."""
    source = db.query(ContentSource).filter(ContentSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Quelle nicht gefunden")

    # Zugehörige News-Items löschen
    db.query(NewsItem).filter(NewsItem.source_id == source_id).delete()
    db.delete(source)
    db.commit()
    return {"message": f"Quelle '{source.name}' und zugehörige Artikel gelöscht"}


@router.patch("/sources/{source_id}/toggle")
async def toggle_source(source_id: int, db: Session = Depends(get_db)):
    """RSS-Quelle aktivieren/deaktivieren."""
    source = db.query(ContentSource).filter(ContentSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Quelle nicht gefunden")

    source.is_active = not source.is_active
    db.commit()
    db.refresh(source)
    return {"id": source.id, "is_active": source.is_active}


# =====================================================
# Scannen
# =====================================================

@router.post("/scan", response_model=ScanResult)
async def scan_all_feeds(db: Session = Depends(get_db)):
    """Alle aktiven RSS-Quellen scannen."""
    result = scan_all_active_feeds(db)
    return result


@router.post("/scan/{source_id}", response_model=list[NewsItemResponse])
async def scan_single_feed(source_id: int, db: Session = Depends(get_db)):
    """Einzelne Quelle scannen."""
    source = db.query(ContentSource).filter(ContentSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Quelle nicht gefunden")
    return scan_feed(source, db)


# =====================================================
# News-Items anzeigen
# =====================================================

@router.get("/items", response_model=list[NewsItemResponse])
async def list_news_items(
    source_id: int | None = Query(None),
    only_unprocessed: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Gescannte News-Artikel auflisten."""
    query = db.query(NewsItem).filter(NewsItem.is_relevant == True)

    if source_id:
        query = query.filter(NewsItem.source_id == source_id)
    if only_unprocessed:
        query = query.filter(NewsItem.is_processed == False)

    return query.order_by(NewsItem.created_at.desc()).limit(limit).all()


@router.delete("/items/{item_id}")
async def delete_news_item(item_id: int, db: Session = Depends(get_db)):
    """Einzelnen News-Artikel löschen."""
    item = db.query(NewsItem).filter(NewsItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Artikel nicht gefunden")
    db.delete(item)
    db.commit()
    return {"message": "Artikel gelöscht"}


# =====================================================
# Post generieren aus News-Artikel
# =====================================================

@router.post("/items/{item_id}/generate", response_model=NewsGenerateResponse)
async def generate_news_post(item_id: int, db: Session = Depends(get_db)):
    """Generiert Instagram + TikTok Content aus einem News-Artikel.
    Quelle wird automatisch im Post vermerkt."""

    item = db.query(NewsItem).filter(NewsItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Artikel nicht gefunden")

    # Quelle laden für Quellenangabe
    source = db.query(ContentSource).filter(ContentSource.id == item.source_id).first()
    source_name = source.name if source else "Unbekannt"

    # Trainingsdaten für News
    training_ig = get_training_examples(db=db, platform="instagram", content_type="news")
    training_tt = get_training_examples(db=db, platform="tiktok", content_type="news")

    # LLM Provider
    provider = get_llm_provider()
    if not await provider.health_check():
        raise HTTPException(status_code=503, detail="LLM Provider nicht erreichbar")

    # Instagram generieren
    ig_prompt = build_news_instagram_prompt(
        title=item.title,
        summary=item.summary or "",
        source_name=source_name,
        source_url=item.url,
        training_examples=training_ig if training_ig else None,
    )
    try:
        ig_raw = await provider._call_ollama(ig_prompt)
        ig_result = parse_instagram_response(ig_raw)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Instagram-Generierung: {str(e)}")

    # TikTok generieren
    tt_prompt = build_news_tiktok_prompt(
        title=item.title,
        summary=item.summary or "",
        source_name=source_name,
        source_url=item.url,
        training_examples=training_tt if training_tt else None,
    )
    try:
        tt_raw = await provider._call_ollama(tt_prompt)
        tt_result = parse_tiktok_response(tt_raw)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TikTok-Generierung: {str(e)}")

    # Als verarbeitet markieren
    item.is_processed = True
    db.commit()

    return NewsGenerateResponse(
        instagram_caption=ig_result["caption"],
        tiktok_description=tt_result["description"],
        provider=provider.get_provider_name(),
        used_training_data=len(training_ig) > 0 or len(training_tt) > 0,
        training_examples_count=max(len(training_ig), len(training_tt)),
    )

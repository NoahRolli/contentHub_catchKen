# app/services/rss_scanner.py
# ============================================================
# RSS-Scanner — scannt Schweizer News-Feeds nach Verkehrsthemen.
# Filtert Artikel nach Keywords und speichert relevante als NewsItem.
# ============================================================

import feedparser
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.content_source import ContentSource
from app.models.news_item import NewsItem


# Standard-Keywords für Verkehrsrelevanz
DEFAULT_KEYWORDS = [
    "unfall", "verkehr", "fahrprüfung", "fahrschule", "führerschein",
    "auto", "motorrad", "velo", "e-bike", "fussgänger",
    "tempolimit", "geschwindigkeit", "alkohol", "steuer",
    "strasse", "autobahn", "kreuzung", "vortritt",
    "polizei", "busse", "bussen", "rasen", "raser",
    "sicherheit", "prävention", "kollision", "crash",
]


def scan_feed(source: ContentSource, db: Session) -> list[NewsItem]:
    """Scannt einen einzelnen RSS-Feed und speichert neue Artikel.

    Args:
        source: Die ContentSource mit der Feed-URL
        db: Datenbank-Session

    Returns:
        Liste der neu gespeicherten NewsItems
    """
    # Feed parsen
    feed = feedparser.parse(source.url)

    if feed.bozo and not feed.entries:
        # Feed konnte nicht gelesen werden
        return []

    # Keywords vorbereiten (aus Quelle oder Standard)
    keywords = DEFAULT_KEYWORDS
    if source.keywords:
        # Eigene Keywords der Quelle haben Vorrang
        keywords = [k.strip().lower() for k in source.keywords.split(",") if k.strip()]

    new_items = []

    for entry in feed.entries:
        title = entry.get("title", "")
        link = entry.get("link", "")
        summary = entry.get("summary", entry.get("description", ""))

        # Duplikat-Check: URL schon gespeichert?
        existing = db.query(NewsItem).filter(NewsItem.url == link).first()
        if existing:
            continue

        # Keyword-Matching: Titel + Summary durchsuchen
        search_text = f"{title} {summary}".lower()
        matched = [kw for kw in keywords if kw in search_text]

        if not matched:
            continue  # Nicht relevant — überspringen

        # Veröffentlichungsdatum parsen
        published_at = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                published_at = datetime(*entry.published_parsed[:6])
            except (ValueError, TypeError):
                pass

        # NewsItem erstellen
        news_item = NewsItem(
            source_id=source.id,
            title=title,
            url=link,
            summary=_clean_html(summary),
            keywords_matched=",".join(matched),
            published_at=published_at,
            is_relevant=True,    # Hat Keyword-Match → relevant
            is_processed=False,  # Noch kein Post generiert
        )

        db.add(news_item)
        new_items.append(news_item)

    # Quelle als gescannt markieren
    source.last_scanned_at = datetime.now()
    db.commit()

    # IDs laden
    for item in new_items:
        db.refresh(item)

    return new_items


def scan_all_active_feeds(db: Session) -> dict:
    """Scannt alle aktiven RSS-Quellen.

    Returns:
        {"scanned": 3, "new_items": 12}
    """
    sources = db.query(ContentSource).filter(
        ContentSource.is_active == True,
        ContentSource.source_type == "rss",
    ).all()

    total_new = 0
    for source in sources:
        new_items = scan_feed(source, db)
        total_new += len(new_items)

    return {"scanned": len(sources), "new_items": total_new}


def _clean_html(text: str) -> str:
    """Entfernt einfache HTML-Tags aus RSS-Summaries."""
    import re
    clean = re.sub(r"<[^>]+>", "", text)
    return clean.strip()

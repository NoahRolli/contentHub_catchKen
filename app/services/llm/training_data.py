# app/services/llm/training_data.py
# ============================================================
# Service zum Laden und Formatieren von Trainingsdaten.
# Wird vom LLM-Provider aufgerufen bevor er einen Prompt baut:
#   1. Gibt es Trainingsdaten für diese Plattform + Content-Type?
#   2. Wenn ja → lade die besten Beispiele
#   3. Formatiere sie als Liste von dicts für den Prompt-Builder
# ============================================================

from sqlalchemy.orm import Session  # Typ für DB-Session
from sqlalchemy import func, desc   # func = SQL-Funktionen, desc = absteigende Sortierung

from app.models.training_post import TrainingPost, Platform, ContentType


# Maximale Anzahl Beispiele die dem LLM mitgegeben werden.
# Mehr Beispiele = besserer Style-Match, aber auch mehr Tokens (= langsamer).
# 5-8 ist ein guter Sweet Spot für Few-Shot Prompting.
MAX_EXAMPLES = 8


def get_training_examples(
    db: Session,
    platform: str,        # "instagram" oder "tiktok"
    content_type: str,     # "success", "news", "theory", "review"
    max_examples: int = MAX_EXAMPLES
) -> list[dict]:
    """
    Lädt Trainings-Posts aus der DB für Few-Shot Prompting.

    Sortiert nach original_date (neueste zuerst), damit der LLM
    den aktuellsten Style lernt — Social Media Style verändert sich!

    Args:
        db: Aktive Datenbank-Session
        platform: Plattform filtern (instagram/tiktok)
        content_type: Content-Typ filtern (success/news/theory/review)
        max_examples: Max Anzahl Beispiele (default: 8)

    Returns:
        Liste von dicts: [{"caption": "...", "hashtags": "..."}]
        Leere Liste wenn keine Trainingsdaten vorhanden.
    """

    # Query bauen: Filtere nach Plattform UND Content-Typ
    # .order_by(desc(...)) = neueste Posts zuerst
    # .limit() = maximal X Ergebnisse
    training_posts = (
        db.query(TrainingPost)
        .filter(
            TrainingPost.platform == platform,       # Nur Instagram ODER TikTok
            TrainingPost.content_type == content_type  # Nur den relevanten Typ
        )
        .order_by(
            # Neueste Posts zuerst — nulls_last() sortiert Posts ohne Datum ans Ende
            desc(TrainingPost.original_date).nulls_last()
        )
        .limit(max_examples)
        .all()  # Ausführen und alle Ergebnisse laden
    )

    # SQLAlchemy-Objekte in einfache dicts umwandeln
    # (der Prompt-Builder braucht nur caption + hashtags)
    return [
        {
            "caption": post.caption,
            "hashtags": post.hashtags  # Kann None sein, wird im Prompt-Builder gehandelt
        }
        for post in training_posts
    ]


def has_training_data(
    db: Session,
    platform: str,
    content_type: str
) -> bool:
    """
    Schneller Check: Gibt es überhaupt Trainingsdaten für diese Kombination?
    Wird z.B. im Frontend angezeigt: "⚡ Few-Shot Modus aktiv" vs "📝 Generischer Modus"

    Nutzt COUNT statt alle Rows zu laden — viel effizienter bei vielen Posts.
    """
    count = (
        db.query(func.count(TrainingPost.id))
        .filter(
            TrainingPost.platform == platform,
            TrainingPost.content_type == content_type
        )
        .scalar()  # .scalar() gibt direkt den Integer-Wert zurück statt ein Tuple
    )

    return count > 0


def get_training_data_stats(db: Session) -> dict:
    """
    Gibt eine Übersicht über alle vorhandenen Trainingsdaten.
    Für den Stats-Endpoint und das Frontend-Dashboard.

    Returns:
        dict mit total_count, by_platform, by_content_type, etc.
    """

    # --- Gesamtanzahl ---
    total = db.query(func.count(TrainingPost.id)).scalar()

    # --- Aufschlüsselung nach Plattform ---
    # GROUP BY platform, dann als dict formatieren
    platform_counts = (
        db.query(TrainingPost.platform, func.count(TrainingPost.id))
        .group_by(TrainingPost.platform)
        .all()
    )
    # Ergebnis: [("instagram", 12), ("tiktok", 3)] → {"instagram": 12, "tiktok": 3}
    by_platform = {str(platform): count for platform, count in platform_counts}

    # --- Aufschlüsselung nach Content-Typ ---
    type_counts = (
        db.query(TrainingPost.content_type, func.count(TrainingPost.id))
        .group_by(TrainingPost.content_type)
        .all()
    )
    by_content_type = {str(ct): count for ct, count in type_counts}

    # --- Ältester und neuester Post ---
    oldest = (
        db.query(func.min(TrainingPost.original_date)).scalar()
    )
    newest = (
        db.query(func.max(TrainingPost.original_date)).scalar()
    )

    return {
        "total_count": total,
        "by_platform": by_platform,
        "by_content_type": by_content_type,
        "has_training_data": total > 0,
        "oldest_post": oldest,
        "newest_post": newest,
    }

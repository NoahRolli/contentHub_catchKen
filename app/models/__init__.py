# __init__.py – Registriert alle Datenbank-Modelle
# Dieser Import ist wichtig: SQLAlchemy muss alle Modelle kennen,
# bevor es die Tabellen in der Datenbank erstellen kann

from app.models.user import User
from app.models.student_success_post import StudentSuccessPost
from app.models.content_source import ContentSource
from app.models.news_item import NewsItem
from app.models.content_idea import ContentIdea
from app.models.scheduled_post import ScheduledPost
from app.models.asset import Asset

# Alle Modelle exportieren – so reicht ein "from app.models import User"
__all__ = [
    "User",
    "StudentSuccessPost",
    "ContentSource",
    "NewsItem",
    "ContentIdea",
    "ScheduledPost",
    "Asset",
]
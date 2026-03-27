# catchKen Content Hub – Auto-generierte Dokumentation

> Automatisch generiert am 27.03.2026 21:41 via GitHub Actions

---

## API-Endpunkte

| Methode | Pfad | Funktion | Beschreibung |
| ------- | ---- | -------- | ------------ |
| `GET` | `/` | `root` | Startseite – zeigt das Frontend mit Formular und Post-Liste. |
| `GET` | `/health` | `health_check` | Wird genutzt um zu prüfen ob der Server läuft. |
| `GET` | `/calendar` | `calendar_page` | Kalender-Ansicht für die Content-Planung. |

---

## Datenbank-Modelle (10 Tabellen)

### Asset
**Datei:** `app/models/asset.py`

Medien-Dateien – Bilder und Videos die zu Posts gehören.

**Felder:** `__tablename__`, `id`, `scheduled_post_id`, `scheduled_post`, `file_path`, `file_name`, `file_type`, `file_size`, `asset_type`, `sort_order`, `created_at`

---

### ContentIdea
**Datei:** `app/models/content_idea.py`

Content-Vorschläge – LLM-generierte Ideen im Wartepool.

**Felder:** `__tablename__`, `id`, `content_type`, `title`, `caption`, `hashtags`, `story_text`, `quiz_data`, `carousel_text`, `tiktok_script`, `source_ref_id`, `source_ref_type`, `is_used`, `is_dismissed`, `created_at`

---

### ContentSource
**Datei:** `app/models/content_source.py`

Content-Quellen – woher das System automatisch Inhalte bezieht.

**Felder:** `__tablename__`, `id`, `name`, `source_type`, `url`, `is_active`, `scan_interval`, `last_scanned_at`, `keywords`, `description`, `created_at`, `updated_at`

---

### NewsItem
**Datei:** `app/models/news_item.py`

Nachrichtenartikel – aus RSS-Feeds extrahierte Artikel.

**Felder:** `__tablename__`, `id`, `source_id`, `source`, `title`, `url`, `summary`, `content_extract`, `published_at`, `keywords_matched`, `is_relevant`, `is_processed`, `prevention_type`, `created_at`

---

### ScheduledPost
**Datei:** `app/models/scheduled_post.py`

Geplante Posts – das Herzstück des Kalenders.

**Felder:** `__tablename__`, `id`, `user_id`, `user`, `content_idea_id`, `content_idea`, `content_type`, `scheduled_date`, `scheduled_time`, `platform`, `caption`, `hashtags`, `story_text`, `status`, `published_at`, `notes`, `created_at`, `updated_at`

---

### StudentSuccessPost
**Datei:** `app/models/student_success_post.py`

Erfolgs-Posts – bestandene Fahrschüler:innen als Social-Media-Content.

**Felder:** `__tablename__`, `id`, `user_id`, `user`, `student_name`, `exam_date`, `category`, `image_path`, `consent_given`, `caption`, `hashtags`, `story_text`, `status`, `created_at`, `updated_at`

---

### Platform
**Datei:** `app/models/training_post.py`

Für welche Plattform ist dieser Trainings-Post?

**Felder:** `INSTAGRAM`, `TIKTOK`

---

### ContentType
**Datei:** `app/models/training_post.py`

Welcher Content-Typ ist der Trainings-Post?

**Felder:** `SUCCESS`, `NEWS`, `THEORY`, `REVIEW`

---

### TrainingPost
**Datei:** `app/models/training_post.py`

Ein einzelner Trainings-Post aus dem echten Instagram/TikTok-Account.

**Felder:** `__tablename__`, `id`, `platform`, `content_type`, `caption`, `hashtags`, `source_url`, `original_date`, `created_at`

---

### User
**Datei:** `app/models/user.py`

Benutzer-Tabelle – speichert Admin-Accounts für das Planungstool.

**Felder:** `__tablename__`, `id`, `email`, `username`, `hashed_password`, `is_active`, `is_admin`, `created_at`, `updated_at`

---

## Projektstruktur
```
app/
├── core/           # Infrastruktur (Config, DB, Security)
├── models/         # Datenbank-Modelle (SQLAlchemy)
├── schemas/        # API Request/Response Formate
├── routers/        # API-Endpunkte
├── services/       # Geschäftslogik
│   └── llm/        # Ollama/OpenAI Integration
├── utils/          # Hilfsfunktionen
└── main.py         # FastAPI Einstiegspunkt
```

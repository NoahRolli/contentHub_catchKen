# catchKen Content Hub

AI-powered social media content planner for Swiss driving schools. Automates content generation for Instagram & TikTok using local LLMs, featuring calendar-based scheduling, RSS-powered news posts, theory content, student success stories, and review highlights.

**Work in Progress – Phase 2 complete**

---

## Demo

> *Screenshots coming soon*

---

## Tech Stack

| Component | Technology |
|---|---|
| Backend | Python 3.13 · FastAPI · SQLAlchemy · SQLite |
| Frontend (MVP) | HTML · CSS · JavaScript |
| Frontend (planned) | React |
| AI | Ollama local (OpenAI as fallback) — switchable |
| Auth | Passlib · bcrypt |
| CI/CD | GitHub Actions (ruff linting · pytest · auto-docs) |

---

## Project Structure
```
catchKen/
├── app/
│   ├── main.py                    # FastAPI entry point
│   │
│   ├── core/                      # Infrastructure
│   │   ├── config.py              # App settings from .env
│   │   ├── database.py            # SQLAlchemy engine & sessions
│   │   └── security.py            # Password hashing (bcrypt)
│   │
│   ├── models/                    # Database models (7 tables)
│   │   ├── user.py                # Admin accounts
│   │   ├── student_success_post.py # Passed students content
│   │   ├── content_source.py      # RSS feeds, Google Reviews
│   │   ├── news_item.py           # Scanned news articles
│   │   ├── content_idea.py        # LLM-generated suggestions
│   │   ├── scheduled_post.py      # Calendar entries
│   │   └── asset.py               # Images, videos
│   │
│   ├── schemas/                   # Pydantic request/response models
│   │   └── student_success.py     # Success post validation
│   │
│   ├── routers/                   # API endpoints
│   │   └── student_success.py     # CRUD for success posts
│   │
│   ├── services/                  # Business logic
│   │   └── llm/                   # Ollama/OpenAI integration (Phase 3)
│   │
│   └── utils/                     # Helper functions
│
├── frontend/
│   ├── static/
│   │   ├── css/style.css          # Main stylesheet
│   │   ├── js/app.js              # Frontend logic
│   │   └── img/
│   └── templates/
│       └── index.html             # Main page with form & post list
│
├── scripts/
│   └── generate_docs.py           # Auto-documentation generator
│
├── docs/
│   ├── content-pipeline.md        # Mermaid pipeline diagrams
│   └── auto-generated.md          # Auto-updated on each push
│
├── tests/
├── media/ → SSD symlink           # Uploads (not in repo)
├── .github/workflows/
│   ├── ci.yml                     # Linting + tests
│   └── docs.yml                   # Auto-generate documentation
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.13+
- Git
- [Ollama](https://ollama.ai) (for local LLM generation, Phase 3)

### Setup
```bash
# Clone the repository
git clone https://github.com/NoahRolli/contentHub_catchKen.git
cd contentHub_catchKen

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env

# Start the server
uvicorn app.main:app --reload
```

### Access

- **App:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **API Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## Features

### Four Content Types
- 🟢 **Success Posts** – Passed driving students with image, caption & hashtags
- 🔴 **News Posts** – Auto-generated from Swiss RSS feeds with safety tips
- 🔵 **Theory Posts** – Swiss driving theory content with quizzes
- 🟡 **Reviews** – Google Reviews repurposed as social media content

### Planning System
- Calendar view (week / 2 weeks / month)
- Drag & drop scheduling
- Status workflow: `DRAFT` → `READY` → `PUBLISHED`
- Sidebar with unplanned content

### Export
- ZIP download with CSV schedule, images, captions & checklist
- No auto-posting in MVP – full editorial control

### Current Status

- [x] Project structure with `app/core/` architecture
- [x] FastAPI server with health check
- [x] Config, database, security foundation
- [x] All 7 database models (User, StudentSuccessPost, ContentSource, NewsItem, ContentIdea, ScheduledPost, Asset)
- [x] Pydantic schemas for validation
- [x] Success posts CRUD (create, read, update, delete)
- [x] Image upload to SSD via symlink
- [x] Consent validation (required for student images)
- [x] Frontend form with post list
- [x] CI pipeline (ruff linting + pytest)
- [x] Auto-generated documentation
- [ ] LLM integration (Ollama for captions & hashtags)
- [ ] Theory post generation
- [ ] RSS news scanning & filtering
- [ ] Google Reviews integration
- [ ] Calendar view with drag & drop
- [ ] ZIP export
- [ ] React frontend migration

---

## Content Pipeline
```mermaid
graph LR
    A[📥 Content Source] --> B[⚙️ Processing]
    B --> C[🤖 LLM Generation]
    C --> D[📝 DRAFT]
    D --> E[👀 Admin Review]
    E --> F[✅ READY]
    F --> G[📤 PUBLISHED]
```

*Detailed diagrams: [docs/content-pipeline.md](docs/content-pipeline.md)*

---

## Roadmap

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Foundation & project structure | ✅ Complete |
| 2 | Success posts CRUD & frontend | ✅ Complete |
| 3 | LLM integration (Ollama) | ⏳ Next |
| 4 | Theory posts | ⏳ Planned |
| 5 | News posts (RSS) | ⏳ Planned |
| 6 | Reviews | ⏳ Planned |
| 7 | Calendar & scheduling | ⏳ Planned |
| 8 | Export & polish | ⏳ Planned |
| 9 | React migration (optional) | ⏳ Planned |

---

## Security

- Secrets in `.env` (never in code or on GitHub)
- Password hashing with bcrypt
- SQLAlchemy ORM (protects against SQL injection)
- Pydantic validation on all inputs
- Consent required for student images
- No full article reproduction (LLM summaries only)

---

## CI/CD

Automated pipelines run on every push to `main`:
- **Linting** with [ruff](https://github.com/astral-sh/ruff)
- **Tests** with pytest (coming soon)
- **Documentation** auto-generated from code

---

## Documentation

- **API Docs (live):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Content Pipeline:** [docs/content-pipeline.md](docs/content-pipeline.md)
- **Auto-generated:** [docs/auto-generated.md](docs/auto-generated.md)

---

## Versioning

This project follows [Semantic Versioning](https://semver.org/):
`v0.1.0` → `v0.2.0` → `v1.0.0`

---

## License

*Not yet defined.*

---

## Author

**Noah Rolli** – [GitHub](https://github.com/NoahRolli)
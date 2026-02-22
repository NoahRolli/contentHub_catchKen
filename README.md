# catchKen Content Hub

A web-based social media content planner for Swiss driving schools. Automates content generation for Instagram & TikTok using local LLMs, featuring calendar-based scheduling, RSS-powered news posts, theory content, student success stories, and review highlights.

## Tech Stack

- **Backend:** Python / FastAPI
- **Database:** SQLite (SQLAlchemy ORM)
- **LLM:** Ollama (OpenAI as fallback)
- **Frontend:** HTML / CSS / JS (React migration planned)

## Setup
```bash
# Clone the repo
git clone https://github.com/NoahRolli/contentHub_catchKen.git
cd contentHub_catchKen

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env

# Run the server
uvicorn app.main:app --reload
```

## Project Status

🚧 Phase 1 – Foundation (in progress)

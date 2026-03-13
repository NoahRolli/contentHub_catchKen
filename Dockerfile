# Dockerfile – Bauanleitung für den catchKen Content Hub Container
# Erstellt ein schlankes Python-Image mit allen Abhängigkeiten

# === Basis-Image: Python 3.13 auf schlankem Debian ===
FROM python:3.13-slim

# === Arbeitsverzeichnis im Container festlegen ===
WORKDIR /app

# === System-Abhängigkeiten installieren ===
# gcc und python3-dev werden für bcrypt (Passwort-Hashing) benötigt
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*  # Cache aufräumen (kleineres Image)

# === Python-Abhängigkeiten installieren ===
# Zuerst nur requirements.txt kopieren (Docker-Cache-Optimierung)
# So werden Pakete nur neu installiert wenn sich requirements.txt ändert
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# === App-Code in den Container kopieren ===
COPY app/ ./app/
COPY frontend/ ./frontend/
COPY scripts/ ./scripts/

# === .env.example als Fallback kopieren (echte .env wird per Volume gemountet) ===
COPY .env.example .env.example

# === Port freigeben (FastAPI Standard) ===
EXPOSE 8000

# === Server starten ===
# --host 0.0.0.0 = von aussen erreichbar (nicht nur localhost)
# --port 8000 = Standard-Port
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
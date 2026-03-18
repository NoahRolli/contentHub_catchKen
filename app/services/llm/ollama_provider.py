# app/services/llm/ollama_provider.py
# ============================================================
# Ollama Provider — spricht mit dem lokalen Ollama Server.
# Ollama läuft standardmässig auf http://localhost:11434
# und stellt verschiedene Modelle bereit (llama3, mistral, etc.)
#
# Dieser Provider implementiert das BaseLLMProvider Interface,
# kann also jederzeit gegen OpenAI ausgetauscht werden.
# ============================================================

import httpx  # Async HTTP Client (moderner als requests, unterstützt async/await)

from app.services.llm.base_provider import BaseLLMProvider
from app.services.llm.prompts import (
    build_instagram_prompt,
    build_tiktok_prompt,
    parse_instagram_response,
    parse_tiktok_response,
)


class OllamaProvider(BaseLLMProvider):
    """
    LLM-Provider der mit einem lokalen Ollama Server kommuniziert.
    Ollama muss separat installiert und gestartet sein:
        $ ollama serve
        $ ollama pull llama3.2
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",  # Standard Ollama Port
        model: str = "llama3.2",                    # Default Modell (kann in .env überschrieben werden)
        timeout: float = 120.0                      # Timeout in Sekunden (LLMs brauchen Zeit!)
    ):
        """
        Args:
            base_url: URL des Ollama Servers
            model: Welches Modell nutzen (llama3.2, mistral, etc.)
            timeout: Max Wartezeit in Sekunden — lokale LLMs auf CPU
                     können 30-60 Sekunden brauchen pro Anfrage
        """
        self.base_url = base_url.rstrip("/")  # Trailing Slash entfernen falls vorhanden
        self.model = model
        self.timeout = timeout

    async def generate_instagram_caption(
        self,
        student_name: str,
        exam_type: str,
        details: str | None = None,
        training_examples: list[dict] | None = None
    ) -> dict:
        """
        Generiert Instagram Caption + Hashtags via Ollama.
        Baut zuerst den Prompt (mit oder ohne Few-Shot),
        schickt ihn an Ollama, und parst die Antwort.

        Returns:
            {"caption": "Herzliche Gratulation...", "hashtags": "#fahrschule #bestanden..."}
        """
        # 1. Prompt bauen (Few-Shot wenn training_examples vorhanden)
        prompt = build_instagram_prompt(
            student_name=student_name,
            exam_type=exam_type,
            details=details,
            training_examples=training_examples
        )

        # 2. An Ollama schicken und Antwort holen
        raw_response = await self._call_ollama(prompt)

        # 3. Antwort parsen (CAPTION: ... HASHTAGS: ... extrahieren)
        return parse_instagram_response(raw_response)

    async def generate_tiktok_description(
        self,
        student_name: str,
        exam_type: str,
        details: str | None = None,
        training_examples: list[dict] | None = None
    ) -> dict:
        """
        Generiert TikTok-Beschreibung via Ollama.
        Gleicher Flow wie Instagram, aber anderer Prompt und Parser.

        Returns:
            {"description": "🔥 Bestanden!!...", "hashtags": "#fyp #fahrschule..."}
        """
        prompt = build_tiktok_prompt(
            student_name=student_name,
            exam_type=exam_type,
            details=details,
            training_examples=training_examples
        )

        raw_response = await self._call_ollama(prompt)
        return parse_tiktok_response(raw_response)

    async def health_check(self) -> bool:
        """
        Prüft ob Ollama läuft und erreichbar ist.
        Ollama antwortet auf GET / mit "Ollama is running".
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(self.base_url)
                # Status 200 = Ollama ist da und antwortet
                return response.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            # Server nicht erreichbar oder Timeout → nicht verfügbar
            return False

    def get_provider_name(self) -> str:
        """Gibt 'ollama' zurück — für Logging und Health-Check."""
        return "ollama"

    # =====================================================
    # PRIVATE METHODE (nicht von aussen aufrufen)
    # =====================================================

    async def _call_ollama(self, prompt: str) -> str:
        """
        Schickt einen Prompt an die Ollama Generate-API und gibt die Antwort zurück.

        Ollama API Endpoint: POST /api/generate
        Body: {"model": "llama3.2", "prompt": "...", "stream": false}

        stream=false → Ollama gibt die komplette Antwort auf einmal zurück
        (statt Token für Token zu streamen). Einfacher zu verarbeiten.

        Args:
            prompt: Der fertige Prompt-String

        Returns:
            Der generierte Text als String

        Raises:
            httpx.HTTPStatusError: Wenn Ollama einen Fehler zurückgibt
            httpx.ConnectError: Wenn Ollama nicht erreichbar ist
        """
        # httpx.AsyncClient als Context Manager → Connection wird am Ende sauber geschlossen
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",  # Ollama Generate Endpoint
                json={
                    "model": self.model,   # z.B. "llama3.2"
                    "prompt": prompt,       # Unser zusammengebauter Prompt
                    "stream": False,        # Komplette Antwort auf einmal (kein Streaming)
                    "options": {
                        "temperature": 0.7,  # Kreativität: 0=robotisch, 1=chaotisch, 0.7=gut für Social Media
                        "top_p": 0.9,        # Nucleus Sampling: 90% der wahrscheinlichsten Tokens berücksichtigen
                    }
                }
            )

            # Fehler werfen wenn Status-Code nicht 2xx ist
            response.raise_for_status()

            # Ollama gibt JSON zurück: {"response": "generierter text...", ...}
            data = response.json()
            return data.get("response", "")  # Sicherheitshalber default="" falls Key fehlt

# app/services/llm/base_provider.py
# ============================================================
# Abstraktes Interface für LLM-Provider (Ollama, OpenAI, etc.)
# Jeder neue Provider muss diese Klasse erben und alle
# abstrakten Methoden implementieren — so können wir
# Provider jederzeit austauschen ohne den Rest anzupassen.
# ============================================================

from abc import ABC, abstractmethod  # ABC = Abstract Base Class, erzwingt Implementation


class BaseLLMProvider(ABC):
    """
    Vertrag für alle LLM-Provider.
    Jeder Provider (Ollama, OpenAI) MUSS diese Methoden implementieren.
    Wenn er es nicht tut, gibt Python einen TypeError beim Instanziieren.
    """

    @abstractmethod
    async def generate_instagram_caption(
        self,
        student_name: str,           # Name des Schülers (z.B. "Lara M.")
        exam_type: str,              # Prüfungstyp (z.B. "Autoprüfung", "Motorrad")
        details: str | None = None,  # Optionale Details (z.B. "beim ersten Versuch")
        training_examples: list[dict] | None = None  # Beispiel-Posts für Few-Shot
    ) -> dict:
        """
        Generiert eine Instagram Caption + Hashtags für einen Erfolgs-Post.

        Args:
            student_name: Name des Fahrschülers
            exam_type: Art der bestandenen Prüfung
            details: Zusätzliche Infos zum Post
            training_examples: Liste von Beispiel-Posts aus der DB
                               Format: [{"caption": "...", "hashtags": "..."}]

        Returns:
            dict mit:
                - "caption": str (der generierte Instagram-Text)
                - "hashtags": str (generierte Hashtags, z.B. "#fahrschule #bestanden")
        """
        pass  # Muss vom konkreten Provider implementiert werden

    @abstractmethod
    async def generate_tiktok_description(
        self,
        student_name: str,
        exam_type: str,
        details: str | None = None,
        training_examples: list[dict] | None = None
    ) -> dict:
        """
        Generiert eine TikTok-Beschreibung für einen Erfolgs-Post.
        TikTok hat einen anderen Style als Instagram — kürzer, punchier,
        mehr Emojis, andere Hashtag-Strategie.

        Returns:
            dict mit:
                - "description": str (die TikTok-Beschreibung)
                - "hashtags": str (TikTok-spezifische Hashtags)
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Prüft ob der Provider erreichbar ist.
        Ollama: Ist der lokale Server am Laufen?
        OpenAI: Ist der API-Key gültig?

        Returns:
            True wenn Provider bereit ist, False wenn nicht
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Gibt den Namen des Providers zurück (z.B. "ollama", "openai").
        Nützlich für Logging und Health-Check Endpoints.
        """
        pass